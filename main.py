from time import sleep
import requests
from bs4 import BeautifulSoup
import json
import os
import glob
import csv
import pprint

prefectures = [
    "tokyo",
]

def make_new_dir():
    #ディレクトリ作成(最初)
    #data- jobs - エリアの数だけフォルダ
    #    - results - エリアの数だけフォルダ 
    for prefecture in prefectures:
        new_dir_path_url = 'data/urls/{}'.format(prefecture)
        new_dir_path_result = 'data/infomations/{}'.format(prefecture)
        os.makedirs(new_dir_path_url, exist_ok=True)
        os.makedirs(new_dir_path_result, exist_ok=True)

#店の情報を取得
def __get_restaurant_info(store_url):
    web_url = 'https://tabelog.com/{}'.format(store_url)

    try:
        r = requests.get(web_url)
        r.raise_for_status()
    except Exception as e:
        return None
    sleep(1)

    soup = BeautifulSoup(r.content, 'lxml')
    
    
    #店名取得
    try:
        store_name = soup.find(class_= 'rstinfo-table__name-wrap').get_text().strip()
    except Exception as e:
        store_name = None
        
    #ジャンル取得
    try:
        store_genure = soup.find("th",string="ジャンル").find_next_sibling("td").get_text().strip()
    except Exception as e:
        store_genure = None
    
    #住所取得
    try: 
        store_adress = soup.find("th",string="住所").find_next_sibling("td").find("p").get_text()
    except Exception as e:
        store_adress = None
      
    #電話番号取得
    try:
        store_phone_num = soup.find(class_ = 'rstdtl-booking-tel-modal__tel-num').get_text().strip()
    except Exception as e:
        store_phone_num = None
        
    #情報をまとめる 
    store_list = [store_name, store_genure, store_adress, store_phone_num]
    
    print(store_list)
    return store_list


def get_and_save_all_areas():
    # それぞれの県の都市を取得
    for prefecture in prefectures:
        write_urls = []

        #サイトの取得
        web_url = 'https://tabelog.com/sitemap/{}/'.format(prefecture)
        try:
            r = requests.get(web_url)
            r.raise_for_status()
            sleep(1)

        except Exception as e:
            print("request is unaccepted! Retry after 60s")
            sleep(60)
            try:
                r = requests.get(web_url)
                r.raise_for_status()
                sleep(1)
            except Exception as e:
                return None

        #urlの取得
        soup = BeautifulSoup(r.content,'lxml')
        write_urls = soup.find(class_='prefarea-content').find_all('a')
            
        #取得したデータの書き込み
        filepath = "data/urls/{}area.csv".format(prefecture)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            for url in write_urls:
                area_url = url.get('href')
                print(area_url)
                writer.writerow([area_url]) 

            
def get_and_save_area_abc():
    #それぞれの県の都市のurlを取得し、50音のurlを取得、書き込み
    for prefecture in prefectures:
        write_urls = []
        read_urls = []

        #urlファイルの読み込み
        filepaths = "data/urls/{}area.csv".format(prefecture)
        with open(filepaths, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                url = row[0]  
                read_urls.append(url)             
        
        for url in read_urls:
            #urlへのリクエストの送信（反応がなかった場合、６０秒待って再送信）
            try:
                r = requests.get(url)
                r.raise_for_status()
                sleep(1)

            except Exception as e:
                print("request is unaccepted! Retry after 60s")
                sleep(60)
                try:
                    r = requests.get(url)
                    r.raise_for_status()
                    sleep(1)
                except Exception as e:
                    return None
            
            #サイトからほしい情報の抽出（50音url）
            soup = BeautifulSoup(r.content,'lxml')
            on_50_url = soup.find_all(class_='sitemap-50on__item-target')

            for url_50 in on_50_url:
                write_urls.append(url_50.get('href'))   

        #取得したurlをファイルに書き込み
        filepath = "data/urls/{}area50on.csv".format(prefecture)      
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)            
            for url in write_urls:
                writer.writerow([url]) 
            
def get_and_save_store():
    #保存した50音のurlから、すべての店のurlを取得

    for prefecture in prefectures:
        
        read_urls = []
        filepaths = "data/area/{}area50on.csv".format(prefecture)
        with open(filepaths, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                read_urls.append(row[0])

        print("urls num:", len(read_urls) )
        
        for url in read_urls:
            #urlへのリクエストの送信（反応がなかった場合、６０秒待って再送信）
            try:
                r = requests.get(url)
                r.raise_for_status()
                sleep(1)

            except Exception as e:
                print("error watiting for 1min")
                sleep(60)
                try:
                    r = requests.get(url)
                    r.raise_for_status()
                    sleep(1)
                except Exception as e:
                    print("error")
                    return None
                
            print(url)
            
            #ページ内にあるurlの数を取得
            soup = BeautifulSoup(r.content,'lxml')
            result_num_element = soup.find(class_="result_num")

            #0件のページがあるため、例外処理
            if result_num_element is not None:
                result_num = int(result_num_element.find("strong").get_text())
                print(result_num)
            else:
                continue
            
            
            #複数ページある場合の処理
            write_urls = [] 

            #200以下の場合がほとんどなので、２００以上の場合は、改めてurlを取得しなおす
            if result_num//200+1 > 1:
                for i in range(result_num//200+1):
                    page = str(i+1)
                    pageurl = url+'?PG={}'.format(page)
                    print(pageurl)

                    try:
                        r = requests.get(pageurl)
                        r.raise_for_status()
                        sleep(1)
                    except Exception as e:
                        print("error watiting for 1min")
                        sleep(60)
                        try:
                            r = requests.get(pageurl)
                            r.raise_for_status()
                            sleep(1)
                        except Exception as e:
                            print("error")
                            return None
                    
                    soup = BeautifulSoup(r.content,'lxml')
                    
                
                #ページ内urlの取得
                web_urls = soup.find(class_="sitemap-50dtl__list").find_all("a")
                for store in web_urls:
                    store_url = store.get("href")
                    print(store_url)
                    write_urls.append(store_url)
                
            #50音(1地域)の処理が終わったら、書き込み
            filepath = "data/area/{}store.csv".format(prefecture)    
            with open(filepath, 'a', newline='') as f:
                writer = csv.writer(f)            
                for wurl in write_urls:
                    writer.writerow([wurl]) 
                
def get_and_save_restaurant_infos():
    for prefecture in prefectures:
    
        #店の情報urlを取得
        store_urls = []
        filepaths = "data/area/{}store.csv".format(prefecture)
        with open(filepaths, 'r') as f:
            reader = csv.reader(f)
            
            for row in reader:
                store_urls.append(row[0])
        
        #ファイルに書き込み
        filepath = "data/results/{}info_utf-8-add.csv".format(prefecture)
        misspath = "data/results/{}miss.csv".format(prefecture)
        misscount = 0
        count = 0
        with open(filepath, 'a', newline='',encoding='utf_8_sig') as f:
            writer = csv.writer(f)  

            #情報を取得
            for store_url in store_urls:
                count += 1
                store_info = __get_restaurant_info(store_url)

                #情報が取れなかった場合
                if store_info == None:
                    miss_url = [count,store_url]

                    #取れなかったindex番号とそのurlをmissファイルに書き込む
                    with open(misspath,'a',newline='') as mf:
                        mwriter = csv.writer(mf)
                        mwriter.writerow(miss_url) 

                    #本ファイルは空行　（これなしで行けるか実験）
                    writer.writerow(store_info)
                    continue
  
                writer.writerow(store_info) 
        
        print("missnum=",misscount)
        print(prefecture ,"is done")


            
            
if __name__ == "__main__":
    #make_new_dir()
    #get_and_save_all_areas()
    #get_and_save_area_abc()
    #get_and_save_store()
    get_and_save_restaurant_infos()
            