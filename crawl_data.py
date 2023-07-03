from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException, TimeoutException
from time import sleep
from random import randint

import pandas as pd
import os
# os.environ['PATH'] += 'C:/Users/User/OneDrive/Documents/personal project/personal project/geckodriver.exe'
url = 'https://www.bol.com'

current_dir = os.getcwd()

driver = Firefox()
driver.get(url)

cookies_dialog = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "js-first-screen-accept-all-button")))
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
    for i in range(1, len(subcategory_items)):
        subcategory_link = subcategory_items[i].find_element(By.TAG_NAME, 'a')
        subcategory_name = subcategory_link.get_attribute('text').strip()
        if (subcategory_name not in ['Telefonieaccessoires', 'Tablets', 'Tabletaccessoires', 'Tassen & Hoezen', 'Dataopslag', 'PC-Gaming', 'Netwerk & Internet','PC-Accessoires']):
        # if (subcategory_name in ['Beamers', 'Software', 'Componenten & Onderdelen']):
            subcategories.append(subcategory_name)

    return subcategories
subcategories = get_product_subcategories('Computers & Accessoires')
print(subcategories)

def navigate_to_category(category, subcategory):
    categorie_menu = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".js_category_menu_button")))
    categorie_menu.click()

    computer_elektronica = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-nav-id="3"]')))        
    computer_elektronica.click()
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

def crawl_product_from_category(category, subcategory):
    navigate_to_category(category, subcategory)
    flag_stop = False
    phone_names = []
    phone_specs = []
    prices = []
    short_descs = []
    other_options = []
    ratings = []
    
    # Scrape the desired information for each product
    while True:
        if flag_stop:
            return category, phone_names, phone_specs, prices, ratings, short_descs, other_options
        product_list = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-list")))
        products = product_list.find_elements(By.CLASS_NAME, "product-item--row")
        if (len(products) == 0):
            flag_stop = True
        for product in products:
            # Scrape phone name
            phone_name, product_specs, main_price, rating, short_desc = "", "", "", "", ""
            try:
                phone_name = product.find_element(By.CLASS_NAME, "product-title").text
            
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
            except NoSuchElementException :
                print("Some elements of product aren't available, setting to empty string")
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
                print("No rollup element available for this product.")
                other_options.append("")

            phone_names.append(phone_name)
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
        except ElementClickInterceptedException:
            sleep(1)
    return category, phone_names, phone_specs, prices, ratings, short_descs, other_options
    

# crawl_product_from_category('Apple iPhones')

def build_pd_categories(subcategories):
    brand = pd.DataFrame()

    brand['category'] = subcategories
    category_mapping = {}

    index = []
    for i in range(1, len(subcategories)+1):
        if i < 10:
            index.append('0' + str(i))
        else:
            index.append(str(i))
        category_mapping[subcategories[i-1]] = i

    brand['category_id'] = index

    return brand, category_mapping

def build_to_product_data(category, phone_names, phone_specs, prices, ratings, short_descs, other_options, category_mapping):
    products = pd.DataFrame()
    products['phone_names'] = phone_names
    products['phone_specs'] = phone_specs
    products['prices'] = prices
    products['ratings'] = ratings
    products['short_descs'] = short_descs
    products['other_options'] = other_options
    products['category_id'] = category_mapping[category]

    return products

brand_data, category_mapping = build_pd_categories(subcategories)
# brand_data.to_csv('personal project/brands_computers.csv', index=False)
# all_products = []
for i, subcategory in enumerate(subcategories):
    print(subcategories[i])
    category, phone_names, phone_specs, prices, ratings, short_descs, other_options = crawl_product_from_category('Computers & Accessoires', subcategory)
    products = build_to_product_data(subcategory, phone_names, phone_specs, prices, ratings, short_descs, other_options, category_mapping)
    print('Appending to product')
    # all_products.append(products)
    if i == 0:
        products.to_csv('personal project/computers_accesories.csv', header=True, index=False)
    else:
        products.to_csv('personal project/computers_accesories.csv', mode='a', header=False, index=False)

# all_products_df = pd.concat(all_products, ignore_index=True)
# all_products_df.to_csv('computers_accesories.csv', index=False)
# print(all_products_df)



# Close the browser
driver.quit()


