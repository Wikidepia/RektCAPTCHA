import json
import math
import time
from random import randint, uniform

import numpy as np
import scipy.interpolate as si
from PIL import Image
from pyclick import HumanCurve
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from rektcaptcha import Rekt

# Initialize selenium, model, class list
rekt = Rekt()
options = webdriver.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(executable_path=r"./chromedriver", options=options)
with open("rc_class.json") as f:
    rc_class = json.load(f)

# Using Bezier Curve for simulate humane like mouse movments
def human_click(start_element=None, end_element=None, target_points=30):
    if start_element is None:
        start_element = driver.find_element_by_xpath("/html")
        start_xy = (randint(30, 60), randint(30, 60))
        action = ActionChains(driver)
        action.move_to_element(start_element)
        action.move_by_offset(start_xy[0], start_xy[1])
        action.perform()
    else:
        start_xy = (start_element.location["x"], start_element.location["y"])
    end_xy = (end_element.location["x"], end_element.location["y"])
    curve_point = HumanCurve(
        start_xy, end_xy, upBoundary=0, downBoundary=0, targetPoints=target_points
    ).points

    current_x = start_xy[0]
    current_y = start_xy[1]
    for curve in curve_point:
        action = ActionChains(driver)
        curve_x = curve[0]
        curve_y = curve[1]
        action.move_by_offset(curve_x - current_x, curve_y - current_y)
        current_x += curve_x - current_x
        current_y += curve_y - current_y
        try:
            action.perform()
        except:  # Handle out-of-bound move
            pass
    end_element.click()


# Randomly sleep
def sleep_uniform(min, max):
    rand = uniform(min, max)
    time.sleep(rand)


def main():
    # Open chromedriver selenium
    driver.get("https://www.google.com/recaptcha/api2/demo")
    driver.switch_to.default_content()
    iframes = driver.find_elements_by_tag_name("iframe")
    driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])

    # Click reCaptcha box
    check_box = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
    )
    human_click(end_element=check_box)

    # Screenshoot image
    sleep_uniform(3, 5)
    driver.switch_to.default_content()
    iframes = driver.find_elements_by_tag_name("iframe")
    driver.switch_to.frame(iframes[2])

    # Check ReCaptcha type
    try:
        instruction = driver.find_element_by_xpath(
            r'//*[@id="rc-imageselect"]/div[2]/div[1]/div[1]/div[2]/span'
        ).text
    except:
        try:
            instruction = driver.find_element_by_class_name(
                r"rc-imageselect-carousel-instructions"
            ).text
        except:
            # 1x verify type
            instruction = None

    if instruction is not None:
        while True:
            correct_tile = solve_captcha()
            click_tiles(correct_tile)

            if (
                instruction != "Click verify once there are none left"
                or len(correct_tile) == 0
            ):
                click_next()

            # Sleep to wait next captcha
            sleep_uniform(3, 5)

            # Check if captcha is solved
            try:
                driver.find_element_by_id(r"recaptcha-verify-button")
            except:
                break
    else:
        correct_tile = solve_captcha()
        click_tiles(correct_tile)
        # Click verify button
        click_next()


def click_next():
    next_button = driver.find_element_by_id(r"recaptcha-verify-button")
    human_click(end_element=next_button)


def solve_captcha():
    global driver
    driver.find_element_by_tag_name("table").screenshot("web_screenshot.png")
    max_column = len(driver.find_elements_by_tag_name("tr"))

    # Inference
    img = Image.open("web_screenshot.png")  # PIL image
    return rekt.inference(img, max_column)


def click_tiles(results):
    global driver
    max_column = len(driver.find_elements_by_tag_name("tr"))

    correct_class = driver.find_element_by_xpath(
        r'//*[@id="rc-imageselect"]/div[2]/div[1]/div[1]/div/strong'
    ).text
    if correct_class in rc_class:
        correct_class = rc_class[correct_class]
    else:
        raise ValueError("This script didnt support that class yet.")

    # Click tiles
    tiles = driver.find_elements_by_tag_name("td")
    tile_column = 0
    tile_row = 1
    old_tile = None
    # TODO : beautify this shit
    for i, tile in enumerate(tiles, 1):
        tile_column += 1
        for result in results:
            if (
                tile_column == result["tile_column"]
                and tile_row == result["tile_row"]
                and result["class"] == correct_class
            ):
                human_click(start_element=old_tile, end_element=tile, target_points=3)
                old_tile = tile
                break
        if i % max_column == 0:
            tile_row += 1
            tile_column = 0


if __name__ == "__main__":
    main()
