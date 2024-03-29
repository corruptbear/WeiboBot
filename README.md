# WeiboBot

新浪微博私信备份导出脚本 （for python3)

2023年更新
仅限网页版登陆下载导出
备份格式为txt文件

## 用法
```bash
#下载本脚本
git clone https://github.com/corruptbear/WeiboBot/
cd WeiboBot
#安装dependency
python3 -m pip install -r requirements.txt
#直接运行以下命令，默认效果: 下载所有非陌生人私信
python3 wbbot.py
```

## 说明

- 网络条件良好, 及时用手机客户端扫码登录, 应该不会有登录方面的问题
- 只要登录cookie有效, 扫过一次码后, 下一次运行脚本, 或调用函数时, 就不用重复扫码.
- 如需要更换登录账号, 删除`cookies.pkl`文件即可, 下一次初始化时会重新扫码.

## API示例
```python
#第一次使用时需要用手机扫码登录 (扫码完毕后命令行界面提示成功，继续运行程序)
b = WeiboBot()
#保存私信(非陌生人私信)
b.get_conversations_all()
#保存和数字id为1234567890的用户的最近2000条私信(实际保存条数会略多)
b.get_conversation(uid="1234567890", max_count=2000)
#获得用户的数字id (炸号/销号后可能无法返回数字id)
uid = b.id_from_screenname("来去之间")
#获得用户的粉丝列表, 最多2000名
b.get_followers(1642909335, max_count=1000, created_since="2023-01-01", created_before="2099-01-01", location_filter="北京")
```