from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException, TimeoutException
from time import sleep
from random import randint
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


import pandas as pd
import os
os.environ['PATH'] += 'C:/Users/User/OneDrive/Documents/Bol_Data_Processing/geckodriver.exe'
# C:\Users\User\OneDrive\Documents\Bol_Data_Processing\geckodriver.exe
url = 'https://www.bol.com'

current_dir = os.getcwd()

driver = Firefox(service=FirefoxService(GeckoDriverManager().install()))
driver.get(url)

cookies_dialog = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "js-first-screen-accept-all-button")))
cookies_dialog.click()
sleep(randint(3, 6))

def get_product_subcategories(target_product):
    # ui-btn ui-btn--primary ui-btn--block@screen-small

    # Find and click the "Categorieën" menu
    categorie_menu = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".js_category_menu_button")))
    categorie_menu.click()

    # Find and hover over the "Computer & Elektronica" category
    computer_elektronica = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-nav-id="3"]')))
    computer_elektronica.click()

    # Find and click the "Telefonie & Tablets" category
    ul_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'//span[contains(text(), "{target_product}")]/../following-sibling::ul[@class="wsp-sub-nav-group__list"]')))

    # Find all the subcategory items within the container
    subcategory_items = ul_element.find_elements(By.TAG_NAME, 'li')
    subcategories = []
    # Skipping a few categories due to different html format
    for i in range (len(subcategory_items) - 1):
        subcategory_link = subcategory_items[i].find_element(By.TAG_NAME, 'a')
        subcategory_name = subcategory_link.get_attribute('text').strip()
        # if (subcategory_name not in ['Telefonieaccessoires', 'Tablets', 'Tabletaccessoires', 'Tassen & Hoezen', 'Dataopslag', 'PC-Gaming', "Printers & Supplies", 'Netwerk & Internet','PC-Accessoires', "Componenten & Onderdelen"]):
        if (subcategory_name in ['Smartphones', 'Tablets', 'Vaste telefoons']):
            subcategories.append(subcategory_name)

    return subcategories
subcategories = get_product_subcategories('Telefonie & Tablets')
print(subcategories)

def navigate_to_category(category, subcategory):
    print('Category', category)
    home = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.omniture_main_logo')))
    home.click()
    sleep(3)

    categorie_menu = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".js_category_menu_button")))

    categorie_menu.click()

    computer_elektronica = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-nav-id="3"]')))  
    # driver.execute_script("arguments[0].scrollIntoView(true);", computer_elektronica)
    # ActionChains(driver).move_to_element(computer_elektronica).perform()
    computer_elektronica.click()
    # sleep(1)
    try:
        telefonie_tablets = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{category}')]")))
    except TimeoutException:
        sleep(1)
        telefonie_tablets = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{category}')]")))

    # ActionChains(driver).move_to_element(telefonie_tablets).perform()
    telefonie_tablets.click()
    category_phone_str = f"//a[contains(text(), '{subcategory}')]"
    category_phone = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, category_phone_str)))
    # ActionChains(driver).move_to_element(category_phone).click().perform()
    # Scroll the element into view
    driver.execute_script("arguments[0].scrollIntoView(true);", category_phone)
    # sleep(randint(3,6))
    category_phone.click()

def scrape_brands():
    brands = []
    more_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-analytics-tag='4842']")))
    more_button.click()
    dialog = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class='searchable-select__section']")))
    for section in dialog:
        # Find all the checkbox input elements
        checkbox_inputs = section.find_elements(By.CSS_SELECTOR, '.searchable-select__item')
        # Extract the options
        new_brands = [checkbox.find_element(By.TAG_NAME, 'label').text for checkbox in checkbox_inputs]
        brands += new_brands
    dialog_close = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='js_close_modal_window modal__window--close-hitarea']")))
    dialog_close.click()
    return brands


def crawl_product_from_category(category, subcategory):
    navigate_to_category(category, subcategory)
    flag_stop = False
    product_names = []
    phone_specs = []
    prices = []
    short_descs = []
    other_options = []
    ratings = []
    brands_names = []
    
    # Scrape the desired information for each product
    iter = 0
    while True:
        if flag_stop:
            return category, product_names, phone_specs, prices, ratings, short_descs, other_options
        product_list = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-list")))
        if iter == 0:
            available_brands = scrape_brands()
            print(available_brands)
        try:
            products = product_list.find_elements(By.CLASS_NAME, "product-item--row")
        except StaleElementReferenceException:
            products = product_list.find_elements(By.CLASS_NAME, "product-item--row")
        if (len(products) == 0):
            flag_stop = True
            break
        for product in products:
            # Scrape phone name
            product_name, product_specs, main_price, rating, short_desc = "", "", "", "", ""
            try:
                brand_name = product.find_element(By.CLASS_NAME, 'product-creator').text
                product_name = product.find_element(By.CLASS_NAME, "product-title").text
            
                # Scrape product specifications 
                product_specs = product.find_element(By.CLASS_NAME, "product-small-specs").text
                # Find the rating div and extract the aria-label attribute value
                rating_div = product.find_element(By.CSS_SELECTOR, 'div[aria-label]')
                rating = rating_div.get_attribute("aria-label") if rating_div else ""
                # Find the price meta tag
                price_meta = product.find_element(By.CSS_SELECTOR, 'meta[itemprop="price"]')
                # Extract the price value from the content attribute
                main_price = price_meta.get_attribute("content") if price_meta else ""

                short_desc_p = product.find_element(By.CSS_SELECTOR, 'p[data-test="product-description"]')

                short_desc = short_desc_p.text if short_desc_p else ""

            # except StaleElementReferenceException:
            #     rating_div = driver.find_element(By.XPATH, "//span[@class='star-rating__rating']")
            #     rating = rating_div.get_attribute("aria-label") if rating_div else ""
            except (StaleElementReferenceException, NoSuchElementException) as e:
                # print("Some elements of product aren't available, setting to empty string")
                pass
            try:
                # Try to find the rollup element
                rollup = product.find_element(By.CLASS_NAME, "rollup")
                
                # Scrape color options and prices
                colors = rollup.find_elements(By.CLASS_NAME, "media__body")
                
                option = {}
                # Iterate over the colors and prices
                for color in colors:
                    color_name = color.find_element(By.TAG_NAME, "div").text
                    price = color.find_element(By.CLASS_NAME, "product-prices__bol-price").text
                    option[color_name] = price
                other_options.append(str(option))

            except (NoSuchElementException, StaleElementReferenceException) as error:
                # print("No rollup element available for this product.")
                other_options.append("")
            brands_names.append(brand_name)
            product_names.append(product_name)
            phone_specs.append(product_specs)
            prices.append(main_price)
            ratings.append(rating)
            short_descs.append(short_desc)
        try:
            next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[aria-label="volgende"]')))
            next_button.click()
            sleep(randint(3,6))
        except (NoSuchElementException, TimeoutException) as error:
            # If the next button is not found, we've reached the last page
            flag_stop = True
            print("No next Button found")
            break
        except (ElementClickInterceptedException, StaleElementReferenceException) as e:
            sleep(1)
        iter += 1
    return available_brands, brands_names, category, product_names, phone_specs, prices, ratings, short_descs, other_options
    

def build_pd_brands(brands, category):
    last_idx = 0
    try:
        df = pd.read_csv('Data crawled/brands_telephones_tablets.csv', delimiter=';')
        print(df['brands_id'].iloc[-1])
        last_idx = int(df['brands_id'].iloc[-1])
    except FileNotFoundError:
        pass
    brands_pd = pd.DataFrame()
    brands_pd['brands'] = brands
    brand_mapping = {}
    index = []
    start = last_idx + 1
    end = len(brands) + last_idx + 1
    for i in range(start, end):
        if i < 10:
            index.append('0' + str(i))
        else:
            index.append(str(i))
        brand_mapping[brands[i-start-1]] = i
    brand_mapping[''] = None
    brands_pd['brands_id'] = index
    brands_pd['category_id'] = category_mapping[category]
    print(brand_mapping)
    return brands_pd, brand_mapping

def build_pd_categories(subcategories):
    category = pd.DataFrame()

    category['category'] = subcategories
    category_mapping = {}

    index = []
    for i in range(1, len(subcategories)+1):
        if i < 10:
            index.append('0' + str(i))
        else:
            index.append(str(i))
        category_mapping[subcategories[i-1]] = i

    category['category_id'] = index

    return category, category_mapping

def build_to_product_data(brands, category, product_name, phone_specs, prices, ratings, short_descs, other_options, category_mapping):
    products = pd.DataFrame()
    products['product_name'] = product_name
    products['phone_specs'] = phone_specs
    products['prices'] = prices
    products['ratings'] = ratings
    products['short_descs'] = short_descs
    products['other_options'] = other_options
    products['category_id'] = category_mapping[category]
    brand_id = []
    for brand in brands:
        if brand == 'Merkloos':
            brand = 'Merkloos / Sans marque'
        if brand not in brand_mapping:
            brand = ""
        brand_id.append(brand_mapping[brand])
    products['brand_id'] = brand_id

    return products

brand_data, category_mapping = build_pd_categories(subcategories)
print(category_mapping)
brand_data.to_csv('Data crawled/category_telephones_tablets.csv', index=False, sep=";")
all_products = []
for i, subcategory in enumerate(subcategories):
    print('Subcategory', subcategories[i])
    # if subcategories[i] in ('Laptops'):
    #     continue
    available_brands, brands, category, product_name, phone_specs, prices, ratings, short_descs, other_options = crawl_product_from_category('Telefonie & Tablets', subcategory)
    brands_pd, brand_mapping = build_pd_brands(available_brands, subcategory)   
    products = build_to_product_data(brands, subcategory, product_name, phone_specs, prices, ratings, short_descs, other_options, category_mapping)
    print('Appending to product')
    # all_products.append(products)
    if subcategories[i] == 'Smartphones':
        # pass
        brands_pd.to_csv('Data crawled/brands_telephones_tablets.csv', header=True, index=False, sep=';')
        products.to_csv('Data crawled/telephones_tablets.csv', header=True, index=False, sep=';')
    else:
        brands_pd.to_csv('Data crawled/brands_telephones_tablets.csv', mode='a', header=False, index=False,  sep=';')
        products.to_csv('Data crawled/telephones_tablets.csv', mode='a', header=False, index=False, sep=';')

# all_products_df = pd.concat(all_products, ignore_index=True)
# all_products_df.to_csv('computers_accesories.csv', index=False)
# print(all_products_df)



# Close the browser
driver.quit()


