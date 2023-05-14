# WeiboBot

新浪微博私信备份导出脚本 （for python3)

2023年更新
仅限网页版登陆下载导出
备份格式为txt文件

用法：
```bash
#默认操作: 下载所有非陌生人私信
python3 wbbot.py
```
如需要更换登录账号,
删除`cookies.pkl`文件即可

API示例
```python
#第一次使用时需要用手机扫码登录 (扫码完毕后关闭二维码图片，继续运行程序)
b = WeiboBot()
#保存私信(非陌生人私信)
b.get_conversations_all()
#保存和数字id为1234567890的用户的最近2000条私信(实际保存条数会略多)
get_conversation(self, uid="1234567890", max_count=2000):
```
