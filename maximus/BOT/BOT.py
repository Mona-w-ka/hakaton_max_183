# bot.py
from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, MessageCallback

from keyboard import get_main_keyboard, segment_keyboard, answer_keyboard
from url_service import URLService
from task_service import TaskService
from config import ML_SERVER_URL, REG_SERVER_URL, token

class BOT:
    def __init__(self, token: str):
        self.bot = Bot(token)
        self.dp = Dispatcher()
        self.url_service = URLService(ML_SERVER_URL)
        self.task_service = TaskService(REG_SERVER_URL)
        
        self.user_states = {}  # user_id → состояние
        self.user_data = {}        # user_id → chat_id, correct_answer и т.д.
        

    async def _on_url_result(self, user_id: int, is_phishing: bool):
        chat_id = self.user_data[user_id]["chat_id"]
    
        if is_phishing is True:
            msg = "🚨 Фишинг! Не переходите по этой ссылке!"
        elif is_phishing is False:
            msg = "✅ Безопасно. Можете переходить по этой ссылке."
        else:
            msg = "❌ Не удалось проверить ссылку. Попробуйте позже."

    # Гарантируем, что msg — непустая строка
        if not msg.strip():
            msg = "Проверка завершена."

        await self.bot.send_message(chat_id=chat_id, text=msg)
        await self.bot.send_message(
            chat_id=chat_id,
            text="Используйте кнопки:",
            attachments=[get_main_keyboard()]  # ← убедитесь, что эта функция возвращает ВАЛИДНУЮ клавиатуру
    )

    async def _handle_start(self, event: MessageCreated):
        uid = event.message.sender.user_id
        cid = event.message.recipient.chat_id
        self.user_data[uid] = {"chat_id": cid}
        self.user_states[uid] = "start"
        await event.message.answer("Привет! Я бот по кибербезопасности! Я могу помочь вам проверить подозрительную ссылку или проверить вашу цифровую граммотность.\n Выберите:", attachments=[get_main_keyboard()])

    async def _handle_callback(self, callback: MessageCallback):
        uid = callback.callback.user.user_id
        cid = callback.message.recipient.chat_id
        action = callback.callback.payload

        if uid not in self.user_data:
            self.user_data[uid] = {"chat_id": cid}

        if action == "check_url":
            self.user_states[uid] = "awaiting_url"
            await callback.message.answer("Пришлите ссылку.")

        elif action == "start_test":
            self.user_states[uid] = "awaiting_segment"
            await callback.message.answer("Выберите группу:", attachments=[segment_keyboard()])

        elif action in {"middle_school", "senior_school", "students", "millennials", "retirees"}:
            if self.user_states.get(uid) == "awaiting_segment":
                # Только если пользователь НЕ зарегистрирован — регистрируем
                if not self.user_data[uid].get("is_registered", False):
                    success_reg = await self.task_service.register_user(uid, action)
                    if not success_reg:
                        await callback.message.answer("❌ Ошибка регистрации.")
                        return
                    self.user_data[uid]["is_registered"] = True

        # Запрашиваем задачу (всегда, даже если уже зарегистрирован)
                success_task, task = await self.task_service.get_task(uid)
                print("FROM BOT")
                print(task)
                if success_task:
            # Перемешиваем здесь
                    import random
                    variants = list(enumerate(task["variants_of_answers"]))
                    random.shuffle(variants)
                    correct = next(i for i, (orig_idx, _) in enumerate(variants, 1) if orig_idx == 0)

                    self.user_states[uid] = "awaiting_answer"
                    self.user_data[uid]["correct_answer"] = correct
                    self.user_data[uid]["explanations"] = task["explanation"]
                    self.user_data[uid]["shuffled"] = variants  # сохраняем

                    msg = f"{task['situation']}\n\n{task['question']}\n"
                    for i, (_, text) in enumerate(variants, 1):
                        msg += f"{i}. {text}\n"
                 
                    await callback.message.answer(msg, attachments=[answer_keyboard()])
                else:
                    await callback.message.answer("❌ Не удалось загрузить задачу.")

        elif action.startswith("answer_"):
            if self.user_states.get(uid) == "awaiting_answer":
                ans = int(action.split("_")[1])
                correct = self.user_data[uid]["correct_answer"]
                exps = self.user_data[uid]["explanations"]
                exp = exps[0] if ans == correct else exps[ans - 1]
                result_msg = f"✅ Верно!\n\n{exp}" if ans == correct else f"❌ Неверно. Правильный ответ: {correct}\n\n{exp}"
                await callback.message.answer(result_msg)
                self.user_states[uid] = "start"
                await callback.message.answer("Используйте кнопки:", attachments=[get_main_keyboard()])

    async def _handle_text(self, event: MessageCreated):
        uid = event.message.sender.user_id
        if self.user_states.get(uid) == "awaiting_url":
            url = event.message.body.text.strip()
            self.user_states[uid] = "start"
            await self.url_service.check_url(url, uid, self._on_url_result)
            
    async def _handle_message(self, event: MessageCreated):
        uid = event.message.sender.user_id
        cid = event.message.recipient.chat_id

    # Если пользователь новый — приветствие
        if uid not in self.user_data:
            self.user_data[uid] = {"chat_id": cid}
            self.user_states[uid] = "start"
            await event.message.answer(
            "Привет! Я бот по кибербезопасности! ...\nВыберите:",
            attachments=[get_main_keyboard()]
        )
            return

    # Если ожидаем URL — обрабатываем
        if self.user_states.get(uid) == "awaiting_url":
            url = event.message.body.text.strip()
            self.user_states[uid] = "start"
            await self.url_service.check_url(url, uid, self._on_url_result)
            return

    # Иначе — напоминаем про кнопки
        await event.message.answer("Используйте кнопки:", attachments=[get_main_keyboard()])

    async def run(self):
        await self.url_service.start()
        self.dp.message_created()(self._handle_message)  # ← ОДИН обработчик
        self.dp.message_callback()(self._handle_callback)
        await self.dp.start_polling(self.bot)
