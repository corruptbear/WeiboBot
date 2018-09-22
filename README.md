# WeiboBot
exporting private chats from weibo 新浪微博私信备份导出

从“微博聊天网页版”导出私信记录，需要安装selenium和chromedriver

备份格式为html文件。会把私信中的图片下载到本地。

用法：
bot=WeiboBot(directory="/Users/zpp/Downloads/weibo",headless=False) #directory是保存备份的文件夹
bot.login(loginname="example@gmail.com",password="123456") #loginname和password是你的账号密码
bot.save_chat(nickname="zhimatang",total_count=1000) #nickname是对方目前的微博昵称，total_count是一次保存的私信条数（从最新一条开始算，可以大于总历史私信条数）
