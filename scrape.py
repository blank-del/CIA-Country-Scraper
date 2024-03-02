import requests
import csv
import pandas as pd
import re
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore")

#Fetch the raw html data from the URL
def fetch_land_boundaries():
    url = "https://www.cia.gov/the-world-factbook/field/land-boundaries/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print("Failed to fetch data. Status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Error:", e)

#Filter out the border total tag
def total_selector(tag):
	return tag.name == "strong" and "total:" in tag.get_text()

#Filter out the border countries tag
def border_countries_selector(tag):
	return tag.name == "strong" and ("border countries" in tag.get_text() or "border sovereign base areas" in tag.get_text() or "regional borders" in tag.get_text())

#Filter out the note tag
def note_selector(tag):
     return tag.name == "strong" and "note:" in tag.get_text()

#Filter out the relevant data i.e. main from the html and then getting pb30 class which holds the country's information
def get_main_data():
    land_boundaries_data = fetch_land_boundaries()
    if land_boundaries_data:
        soup = BeautifulSoup(land_boundaries_data, 'html.parser')
        soup = soup.find('body').find('main')
        #Sample Country Data
        '''
        <div class="pb30">
            <h3 class="mt10">
                <a href="/the-world-factbook/countries/tajikistan/">
                Tajikistan
                </a>
            </h3>
            <strong>
                total:
            </strong> 
                4,130 km
            <br/>
            <br/>
            <strong>
                border countries (4):
            </strong>
            Afghanistan 1,357 km; China 477 km; Kyrgyzstan 984 km; Uzbekistan 1,312 km 
        </div>
        '''
        return soup.find_all('div', class_='pb30')

def get_country_name(tag):
    return tag.find('a').text.strip()

def get_country_total_border(tag):
    total_border = 0
    if tag.find(total_selector) is not None:
        total_border = tag.find(total_selector).next_sibling.strip().replace(",", "").replace("km", "").strip()
    return total_border

def get_country_note(tag):
    note = ''
    if tag.find(note_selector) is not None:
        note = tag.find(note_selector).next_sibling.strip()
    return note

def get_border_data():
    country_divs = get_main_data()
    columns = ['Country_Name', 'data']
    border_list = []
    for i in range(1, len(country_divs)):
        if country_divs[i].find(border_countries_selector) is not None:
            country_list = country_divs[i].find(border_countries_selector).next_sibling.strip()
            pattern = r"(\d{1,3}(?:,\d{3})?\s*km)"
            comma_removed = re.sub(pattern, lambda m: m.group().replace(',', ''), country_list)
            additional_info_removed = re.sub(r'(\([a-zA-Z\s]*\d+ km.*?\))', '', comma_removed)
            splitting_country_regions = re.sub(r'(\d+\s*km)\s+and\s+', r'\1;', additional_info_removed)
            split_list = splitting_country_regions.replace(",", ";").split(';')
            split_list_clean = []
            for j in range (len(split_list)):
                if 'km' in split_list[j]:
                    split_list_clean.append(split_list[j].strip())
            data = pd.DataFrame({'country_cca3': get_country_name(country_divs[i]), 'data': split_list_clean})
            border_list.append(data)
    return (border_list)

def clean_border_country(x):
    return x.replace("km", "").strip()

borders_df = pd.concat(get_border_data(), axis=0)
borders_df['data'] = borders_df['data'].apply(clean_border_country)

def get_length(x):
    return x.split(' ')[-1]

def get_border_country(x):
    return x.replace(get_length(x),"").strip()

def write_borders_info():
    borders_df['border_country'] = borders_df['data'].apply(get_border_country)
    borders_df['border_length'] = borders_df['data'].apply(get_length)
    borders_df.drop(columns=['data'], inplace=True)
    borders_df.to_csv('borders_info.csv', sep='|', index=False)


def write_country_info():
    country_divs = get_main_data()
    data_list = []
    for i in range(1, len(country_divs)):
        data ={
            'country_cca3' : get_country_name(country_divs[i]),
            'border_total' : get_country_total_border(country_divs[i]),
            'notes' : get_country_note(country_divs[i])
        }
        data_list.append(data)
    pd.DataFrame(data_list).to_csv('countries_info.csv', sep='|', index=False)
        

write_country_info()
write_borders_info()