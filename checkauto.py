import requests
import json
import os

try:
    from pypushdeer import PushDeer
    HAS_PUSHDEER = True
except ImportError:
    HAS_PUSHDEER = False

# -------------------------------------------------------------------------------------------
# 企业微信推送函数
# -------------------------------------------------------------------------------------------
def send_wechat_work(webhook_url, title, content):
    """企业微信机器人推送"""
    data = {
        "msgtype": "text",
        "text": {
            "content": f"{title}\n\n{content}"
        }
    }
    
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        result = response.json()
        if result.get('errcode') == 0:
            print("企业微信推送成功")
            return True
        else:
            print(f"企业微信推送失败: {result.get('errmsg')}")
            return False
    except Exception as e:
        print(f"企业微信推送异常: {e}")
        return False

# -------------------------------------------------------------------------------------------
# PushDeer推送函数
# -------------------------------------------------------------------------------------------
def send_pushdeer(sckey, title, content):
    """PushDeer推送"""
    if not HAS_PUSHDEER:
        print("未安装 pypushdeer 库，跳过 PushDeer 推送")
        return False
    
    try:
        pushdeer = PushDeer(pushkey=sckey)
        pushdeer.send_text(title, desp=content)
        print("PushDeer 推送成功")
        return True
    except Exception as e:
        print(f"PushDeer 推送异常: {e}")
        return False

# -------------------------------------------------------------------------------------------
# 主程序
# -------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # PushDeer key 申请地址 https://www.pushdeer.com/product.html
    sckey = os.environ.get("SENDKEY", "")
    
    # 企业微信机器人 Webhook 地址
    wechat_webhook = os.environ.get("WECHAT_WEBHOOK", "")

    # 推送内容
    title = ""
    success, fail, repeats = 0, 0, 0        # 成功账号数量 失败账号数量 重复签到账号数量
    context = ""

    # glados账号cookie 直接使用数组 如果使用环境变量需要字符串分割一下
    cookies = os.environ.get("COOKIES", "").split("&")
    if cookies[0] != "":

        check_in_url = "https://glados.cloud/api/user/checkin"        # 签到地址
        status_url = "https://glados.cloud/api/user/status"          # 查看账户状态

        referer = 'https://glados.cloud/console/checkin'
        origin = "https://glados.cloud"
        useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        payload = {
            'token': 'glados.cloud'
        }
        
        for cookie in cookies:
            checkin = requests.post(check_in_url, headers={'cookie': cookie, 'referer': referer, 'origin': origin,
                                    'user-agent': useragent, 'content-type': 'application/json;charset=UTF-8'}, data=json.dumps(payload))
            state = requests.get(status_url, headers={
                                'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent})

            message_status = ""
            points = 0
            message_days = ""
            
            
            if checkin.status_code == 200:
                # 解析返回的json数据
                result = checkin.json()     
                # 获取签到结果
                check_result = result.get('message')
                points = result.get('points')

                # 获取账号当前状态
                result = state.json()
                # 获取剩余时间
                leftdays = int(float(result['data']['leftDays']))
                # 获取账号email
                email = result['data']['email']
                
                print(check_result)
                if "Checkin! Got" in check_result:
                    success += 1
                    message_status = "签到成功，会员点数 + " + str(points)
                elif "Checkin Repeats!" in check_result:
                    repeats += 1
                    message_status = "重复签到，明天再来"
                else:
                    fail += 1
                    message_status = "签到失败，请检查..."

                if leftdays is not None:
                    message_days = f"{leftdays} 天"
                else:
                    message_days = "error"
            else:
                email = ""
                message_status = "签到请求URL失败, 请检查..."
                message_days = "error"

            context += "账号: " + email + ", P: " + str(points) +", 剩余: " + message_days + " | "

        # 推送内容 
        title = f'Glados, 成功{success},失败{fail},重复{repeats}'
        print("Send Content:" + "\n", context)
        
    else:
        # 推送内容 
        title = f'# 未找到 cookies!'

    print("sckey:", sckey)
    print("wechat_webhook:", wechat_webhook)
    print("cookies:", cookies)
    
    # 推送消息
    push_count = 0
    
    # PushDeer 推送
    if sckey:
        if send_pushdeer(sckey, title, context):
            push_count += 1
    else:
        print("未设置 SENDKEY，跳过 PushDeer 推送")
    
    # 企业微信推送
    if wechat_webhook:
        if send_wechat_work(wechat_webhook, title, context):
            push_count += 1
    else:
        print("未设置 WECHAT_WEBHOOK，跳过企业微信推送")
    
    if push_count == 0:
        print("未配置任何推送方式")