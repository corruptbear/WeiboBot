#!/usr/local/bin/python3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from datetime import date
import os
import glob

class WeiboBot:
    base_url = "http://weibo.com/login.php"
    driver_path = "/usr/local/bin/chromedriver" #modify this if necessary
    
    def __init__(self,directory,headless=False):
        self.directory=directory
        chromeOptions = webdriver.ChromeOptions()
        prefs = {"download.default_directory":self.directory,"download.prompt_for_download":False,"download.directory_upgrade":True,"safebrowsing.enabled":True}
        chromeOptions.add_experimental_option("prefs",prefs)
        if headless:
            chromeOptions.add_argument("headless")
            chromeOptions.add_argument('window-size=1200x800')
        self.driver = webdriver.Chrome(WeiboBot.driver_path, chrome_options=chromeOptions) 
        #self.driver = webdriver.Chrome(chrome_options=chromeOptions)
        self.driver.get(WeiboBot.base_url)
        sleep(2)            
    
    def login(self,loginname,password):  
        """log into your weibo account
        """           
        #wait = WebDriverWait(self.driver, 10)
        #loginname_input = wait.until(EC.element_to_be_clickable((By.ID, "loginname")))
        self.driver.find_element_by_id("loginname").clear()
        self.driver.find_element_by_id("loginname").send_keys(loginname)
        self.driver.find_element_by_xpath("//*[@id='pl_login_form']/div/div[3]/div[2]/div/input").clear()
        self.driver.find_element_by_xpath("//*[@id='pl_login_form']/div/div[3]/div[2]/div/input").send_keys(password)
        self.driver.find_element_by_xpath("//*[@id='pl_login_form']/div/div[3]/div[6]/a").click()
        sleep(2)        
        
    def save_chat(self,nickname,total_count): 
        """export and save your private messages with specific user
           Keyword arguments:
           nickname -- the weibo nickname of that specific user, can be in pinyin. make sure when you type it into the 
                       search box on https://api.weibo.com/chat/#/main , only that specific user is shown
           total_count -- the total number of private messages you want to save. 
        """   
        PAUSE_TIME=0.1 #unit:s
        BATCH_SIZE=100
        TIME_OUT=60 #unit:s
        
        chat_area_found=False
        num_of_tries=10
        
        while chat_area_found==False:
            self.driver.get("https://api.weibo.com/chat/#/main")
            sleep(2)
        
            search_box=self.driver.find_element_by_xpath("//*[@id='contacts_panel']/div[2]/div[1]/input")
            search_box.clear()
            sleep(1)
            search_box.send_keys(nickname)
            sleep(1.5)
            
            try:
                self.driver.find_element_by_xpath("//*[@id='contacts_panel']/div[2]/div[4]/ul[1]/li/div[1]").click()
            except Exception:
                num_of_tries-=1
                if num_of_tries>=0:
                    print('re-try load chat_area')
                    continue
                else:
                    print('failed to load chat_area after multiple tries.')
                    self.driver.quit()
            
            chat_area_found=True
      
        chat_area=self.driver.find_element_by_class_name("W_dialogue_cont")
        chat_area.click()
        sleep(1)
        
        self.driver.execute_script("document.body.style.zoom='60%'")
        
        bubbles=chat_area.find_elements_by_class_name("bubble_bottom")

        old_count=0
        new_count=len(bubbles)
        no_update=0

        while new_count<total_count and no_update<max(TIME_OUT/(PAUSE_TIME*BATCH_SIZE),1):
            old_count=new_count
            
            for i in range(BATCH_SIZE):
                chat_area.send_keys(Keys.CONTROL+Keys.HOME)
                sleep(PAUSE_TIME)
                
            bubbles=chat_area.find_elements_by_class_name("bubble_bottom")      
            new_count=len(bubbles)
            print("current count:",new_count)
            
            if old_count==new_count:
                no_update+=1
                if no_update%2==1:
                    self.driver.execute_script("document.body.style.zoom='125%'")
                else:
                    self.driver.execute_script("document.body.style.zoom='80%'")
            else:
                no_update=0
        
        sleep(1)
        
        users=chat_area.find_elements_by_class_name("bubble_user")   

        pairs=list(zip(users[len(users)-min(len(users),len(bubbles)):],bubbles[len(bubbles)-min(len(users),len(bubbles)):]))
        
        print("total number of bubbles:",len(pairs))       
        
        if len(pairs)>total_count:
            pairs=pairs[len(pairs)-total_count:]
            
        chunk_size=len(pairs)//max(len(pairs)//1000,1)+1
        
        for i in range(0,len(pairs),chunk_size):
            end_index=min(i+chunk_size,len(pairs))
            path=self.directory+'/'+nickname+'-'+str(date.today())+'-'+str(i+1)+'-'+str(end_index)+'.html'
            self.write_html(pairs[i:end_index],path)
        
        self.driver.quit()
        
        
    def write_html(self,users_bubbles_pairs,filepath):  
        f = open(filepath,'w')  
        print('writing to...',filepath)     

        message_head = """<html>
        <head><meta charset='utf-8'>
        <style>.holder img {max-height: 250px;max-width: 250px;}</style>
        <body>
        """
        
        message_tail="</body></html>"
        message_body=""
                      
        for p in users_bubbles_pairs:           
            #self.driver.execute_script("return arguments[0].scrollIntoView();", p[0])
            #self.driver.execute_script("return arguments[0].scrollIntoView();", p[1])
            title=p[0].find_element_by_class_name("face").get_attribute("title")
            content_type=p[1].find_element_by_xpath(".//div").get_attribute("class")
                        
            message_body+="<p>"+title+"  "
            
            if content_type=="img_mod ":
                adrString1=p[1].find_element_by_xpath(".//div/img").get_attribute("ng-click")
                adrString2=p[1].find_element_by_xpath(".//div/img").get_attribute("src")
                img_url=adrString1[adrString1.find("https"):adrString1.find("fid")+4] + adrString2[adrString2.find("fid")+4:adrString2.find("&high")]             
                print("Getting Image from...",img_url)
                self.driver.get(img_url)
                sleep(0.5)

                list_of_files = glob.glob(self.directory+'/*')
                filename = max(list_of_files, key=os.path.getctime)
                if filename.find(".crdownload")!=-1: #downloading
                    filename=filename[:filename.find(".crdownload")]
                print("Downloading Image:",filename)
                
                message_body+='''<figure class="holder"><img src="'''+filename+'''"></figure>'''+"</p>"+"\n"
                
            if content_type=="bubble_cont":
                innerHTML=p[1].find_element_by_xpath(".//div/div[2]/div/p").get_attribute('innerHTML')         
                message_body+=innerHTML+"</p>"+"\n"

        message=message_head+message_body+message_tail
        f.write(message)
        f.close() 
              
######################## 
#Usage Template  
'''
bot=WeiboBot(directory="/Users/zpp/Downloads/weibo",headless=False) #please modify this
bot.login(loginname="example@gmail.com",password="123456") #please modify this
bot.save_chat(nickname="zhimatang",total_count=1000) #please modify this
'''


