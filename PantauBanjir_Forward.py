from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def setup_driver():
    """Setup and configure the WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Set up the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def select_date(driver, target_date):
    """Select a specific date using the calendar widget
    
    Args:
        driver: WebDriver instance
        target_date: datetime object representing the date to select
    """
      # Indonesian month names
    month_names_id = {
        1: "Januari",
        2: "Februari",
        3: "Maret",
        4: "April",
        5: "Mei",
        6: "Juni",
        7: "Juli",
        8: "Agustus",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Desember"
    }

    # Click on the date picker button/icon to open the calendar
    date_picker_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[3]/div[2]/div[1]/div[2]/div[1]/button"))
    )
    date_picker_button.click()
    time.sleep(1)  # Wait for calendar to open

    # Get target month and year in Indonesian
    target_month_id = month_names_id[target_date.month]
    target_year = target_date.year
    target_month_year_id = f"{target_month_id} {target_year}"  # e.g., "April 2025"
    
    # Navigate to the correct month/year
    # First, check if we need to navigate to a different month/year
    current_month_year = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[3]/div[2]/div[1]/div[2]/div[1]/div/div/div/div[2]/header"))
    ).text
    
    target_month_year = target_date.strftime("%B %Y")  # e.g., "April 2025"
    
    # Navigate to the target month and year if needed
    # Using your suggestion of PageUp/PageDown for navigation
    while target_month_year_id not in current_month_year:
        if target_date.year < int(current_month_year.split()[-1]) or \
           (target_date.year == int(current_month_year.split()[-1]) and 
            list(month_names_id.values()).index(target_month_id) < list(month_names_id.values()).index(current_month_year.split()[0])):
            # Target date is in the past, use PageUp
            prev_button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[3]/div[2]/div[1]/div[2]/div[1]/div/div/div/div[1]/button[2]")
            prev_button.click()
        else:
            # Target date is in the future, use PageDown
            next_button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[3]/div[2]/div[1]/div[2]/div[1]/div/div/div/div[1]/button[4]")
            next_button.click()
        
        time.sleep(0.5)  # Wait for calendar to update
        
        # Update current month/year
        current_month_year = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[3]/div[2]/div[1]/div[2]/div[1]/div/div/div/div[2]/header"))
        ).text
    
    # Click on the target day
    formatted_date = target_date.strftime("%Y-%m-%d")
    
    # Click on the target day based on the data-date attribute
    try:
        day_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@data-date='{formatted_date}']"))
        )
        day_element.click()
    except:
        # Alternative approach using the cell ID pattern from your screenshot
        try:
            # The pattern seems to be "_BVID__79_cell-YYYY-MM-DD_"
            formatted_cell_date = target_date.strftime("%Y-%m-%d")
            day_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[contains(@id, 'cell-{formatted_cell_date}')]"))
            )
            day_element.click()
        except:
            # Final fallback - try to find by the aria-label which contains the date in Indonesian
            month_names_id = {
                1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
            }
            day_names_id = {
                0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"
            }
            
            # Create the Indonesian date format as seen in aria-label
            day_of_week = day_names_id[target_date.weekday()]
            formatted_aria_date = f"{day_of_week}, {target_date.day} {month_names_id[target_date.month]} {target_date.year}"
            
            day_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@aria-label='{formatted_aria_date}']"))
            )
            day_element.click()
    
    # Wait for the page to update after date selection
    time.sleep(2)

def extract_table_data(driver, current_date):
    """Extract data from the table for the current date
    
    Args:
        driver: WebDriver instance
        current_date: datetime object of the current date being processed
        
    Returns:
        pandas DataFrame with the extracted data
    """
    # Wait for the table to be visible
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[3]/div[2]/div[2]/div[1]/div/div/table"))
    )
    
    # Extract table headers
    headers = []
    header_elements = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[3]/div[2]/div[2]/div[1]/div/div/table/thead/tr/th")
    for header in header_elements:
        headers.append(header.text)
    
    # Extract table rows
    rows = []
    row_elements = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[3]/div[2]/div[2]/div[1]/div/div/table/tbody/tr")
    
    for row in row_elements:
        cell_elements = row.find_elements(By.XPATH, "./td")
        row_data = [cell.text for cell in cell_elements]
        rows.append(row_data)
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)
    
    
    return df

def main():
    # Define date range for scraping - 3 months example
    start_date = datetime(2024, 12, 1)  # January 1, 2023
    end_date = datetime(2025, 4, 9)   # March 31, 2023
    
    # Initialize WebDriver
    print("Initializing WebDriver...")
    driver = setup_driver()
    
    # URL of the water level monitoring website
    url = "https://pantaubanjir.jakarta.go.id/"  # Replace with actual URL
    
    # Navigate to the website
    print(f"Navigating to {url}...")
    driver.get(url)
    
    # Process data month by month
    current_date = start_date
    while current_date <= end_date:
        # Determine the last day of the current month
        if current_date.month == 12:
            month_end = datetime(current_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(current_date.year, current_date.month + 1, 1) - timedelta(days=1)
        
        # Ensure month_end doesn't exceed the overall end_date
        month_end = min(month_end, end_date)
        
        # List to store DataFrames for the current month
        month_data = []
        
        # Process each date in the current month
        process_date = current_date
        while process_date <= month_end:
            try:
                print(f"Processing data for {process_date.strftime('%Y-%m-%d')}...")
                
                # Select the date in the website
                select_date(driver, process_date)
                
                # Extract table data
                df = extract_table_data(driver, process_date)
                
                # Add to our collection for the current month
                month_data.append(df)
                
                # Move to next date
                process_date += timedelta(days=1)
                
            except Exception as e:
                print(f"Error processing {process_date.strftime('%Y-%m-%d')}: {str(e)}")
                # Continue with the next date even if there's an error
                process_date += timedelta(days=1)
        
        # Combine and export the current month's data
        if month_data:
            # Create output directory if it doesn't exist
            output_dir = "water_level_data"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Combine the month's data
            month_df = pd.concat(month_data, ignore_index=True)
            
            # Generate output filename for the month
            month_file = os.path.join(
                output_dir, 
                f"water_level_data_{current_date.strftime('%Y_%m')}.xlsx"
            )
            
            # Export to Excel
            print(f"Exporting data for {current_date.strftime('%B %Y')} to {month_file}...")
            month_df.to_excel(month_file, index=False)
            print(f"Data successfully exported to {month_file}")
            
            # Clear the month data to free up memory
            month_data = []
        
        # Move to the first day of next month
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)
    
    # Close the browser
    driver.quit()

if __name__ == "__main__":
    main()