import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# 创建机器人实例
bot = telegram.Bot(token='5962117198:AAEva6k564IEop3NP7CkFUimqjNVkRDJw7Q')

# 创建消息处理器实例
updater = Updater(token='5962117198:AAEva6k564IEop3NP7CkFUimqjNVkRDJw7Q', use_context=True)
dispatcher = updater.dispatcher

# 存储投稿信息的字典
posts = {}

# 存储管理员信息的列表
admins = []

# 是否开启自动审核
auto_approve_enabled = False

# 注意事项列表
notice_list = []

# 添加注意事项
def add_notice(update, context):
    notice_text = " ".join(context.args)
    notice_list.append(notice_text)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"已添加注意事项：\n{notice_text}")

# 删除指定编号的注意事项
def del_notice(update, context):
    notice_index = int(context.args[0]) - 1
    if notice_index >= len(notice_list) or notice_index < 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="不存在该编号的注意事项。")
        return
    notice_text = notice_list.pop(notice_index)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"已删除注意事项：\n{notice_text}")

# 修改指定编号的注意事项
def modify_notice(update, context):
    notice_index = int(context.args[0]) - 1
    if notice_index >= len(notice_list) or notice_index < 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="不存在该编号的注意事项。")
        return
    notice_text = " ".join(context.args[1:])
    notice_list[notice_index] = notice_text
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"已修改注意事项为：\n{notice_text}")

# 处理 /start 命令
def start(update, context):
    # 发送注意事项
    if len(notice_list) > 0:
        notice_text = "\n\n".join([f"{i+1}. {notice}" for i, notice in enumerate(notice_list)])
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"注意事项：\n{notice_text}")
        # 等待用户同意
        context.bot.send_message(chat_id=update.effective_chat.id, text="请确认是否同意以上注意事项（输入“同意”或“不同意”）：")
        return
    context.bot.send_message(chat_id=update.effective_chat.id, text="欢迎来到频道投稿机器人！\n请发送你想要投稿的内容。")

# 处理用户同意或不同意注意事项
def agree_notice(update, context):
    message_text = update.message.text.lower()
    user_id = update.message.from_user.id
    if message_text == "同意":
        # 用户同意，允许投稿
        if auto_approve_enabled or user_id in admins:
            context.bot.send_message(chat_id=update.effective_chat.id, text="您已同意注意事项，可以开始投稿了哦！")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="管理员需要开启自动审核或手动审核通过才能进行投稿。")
    elif message_text == "不同意":
        # 用户不同意，禁止投稿
        posts.pop(user_id, None)
        context.bot.send_message(chat_id=update.effective_chat.id, text="您已拒绝注意事项，无法进行投稿哦！若想解封请联系管理员使用“/unban [被封禁人员ID]”指令进行解封。")

# 处理投稿逻辑
def post_handler(update, context):
    user_id = update.message.from_user.id
    # 判断是否允许投稿
    if auto_approve_enabled or user_id in admins:
        # 获取用户信息和投稿类型
        user = update.message.from_user
        text = update.message.text
# 存储用户投稿信息
        posts[user_id] = {
            "user_id": user_id,
            "username": user.username,
            "name": user.first_name + " " + user.last_name if user.last_name else user.first_name,
            "text": text,
            "approved": not auto_approve_enabled and user_id not in admins,  # 自动审核开启时默认为 True，管理员发布的消息也默认为 True
        }
        # 发送提示信息
        if auto_approve_enabled:
            context.bot.send_message(chat_id=update.effective_chat.id, text="已收到您的投稿，将自动审核并发布。")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="已收到您的投稿，请等待管理员审核。")

# 处理 /approve 命令
def approve(update, context):
    user_id = int(context.args[0])
    if user_id not in posts:
        context.bot.send_message(chat_id=update.effective_chat.id, text="该用户没有投过稿。")
        return
    posts[user_id]["approved"] = True
    post = posts[user_id]
    # 发送已审核通过的消息
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"已审核通过以下投稿：\n{post['username']}({post['name']})：{post['text']}")

# 处理 /unban 命令
def unban(update, context):
    user_id = int(context.args[0])
    if user_id not in posts:
        context.bot.send_message(chat_id=update.effective_chat.id, text="该用户没有被封禁。")
        return
    posts[user_id]["approved"] = False
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"已解封用户 {user_id}，请让他重新阅读注意事项并同意。")

# 处理 /list 命令
def list_posts(update, context):
    post_list = [f"{post['username']}({post['name']})：{post['text']}" for post in posts.values() if post["approved"]]
    if len(post_list) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="暂无已发布的投稿。")
        return
    post_text = "\n\n".join(post_list)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"已发布的投稿：\n{post_text}")

# 处理 /autoapprove 命令
def toggle_auto_approve(update, context):
    global auto_approve_enabled
    auto_approve_enabled = not auto_approve_enabled
    if auto_approve_enabled:
        context.bot.send_message(chat_id=update.effective_chat.id, text="已开启自动审核模式。")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="已关闭自动审核模式。")

# 将消息处理器添加到机器人实例中
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text, post_handler))
dispatcher.add_handler(CommandHandler("approve", approve, filters=Filters.user(username=admins)))
dispatcher.add_handler(CommandHandler("unban", unban, filters=Filters.user(username=admins)))
dispatcher.add_handler(CommandHandler("list", list_posts, filters=Filters.user(username=admins)))
dispatcher.add_handler(CommandHandler("autoapprove", toggle_auto_approve, filters=Filters.user(username=admins)))
dispatcher.add_handler(CommandHandler("add_notice", add_notice, filters=Filters.user(username=admins)))
dispatcher.add_handler(CommandHandler("del_notice", del_notice, filters=Filters.user(username=admins)))
dispatcher.add_handler(CommandHandler("modify_notice", modify_notice, filters=Filters.user(username=admins)))
dispatcher.add_handler(MessageHandler(Filters.text(["同意", "不同意"]), agree_notice))

# 启动机器人
updater.start_polling()
watermark_preview = tk.Label(canvas_preview, text="Watermark Preview", font=("Arial", 16))

然后在终端中运行该文件即可启动 Telegram 机器人。如果需要导出代码，你只需要将这段代码复制到 Python 文件中保存即可。