# url_service.py
import asyncio
import httpx

class URLService:
    def __init__(self, base_url):
        self.base_url = base_url
        self.pending = {}  # url → (user_id, callback)
        self.lock = asyncio.Lock()
        self.client = httpx.AsyncClient(timeout=10.0)

    async def check_url(self, url, user_id, result_callback):
        clean_url = url if url.startswith(('http://', 'https://')) else f'https://{url}'
        try:
            # Отправляем POST на /check с телом {"url": "..."}
            
            response = await self.client.post(
                f"{self.base_url}/check",
                json={"url": clean_url}
            )
            response.raise_for_status()
            data = response.json()
            
            # Предполагаем, что ответ: {"is_phishing": true} или {"prediction": 1}
            # Адаптируем под ваш формат:
            
            is_phishing = None
            
            if "is_phishing" in data:
                is_phishing = bool(data["is_phishing"])
            elif "prediction" in data:
                is_phishing = data["prediction"] == 1
            elif "result" in data:
                is_phishing = data["result"] == 1
            else:
                # Если формат неизвестен — логика по умолчанию
                
                is_phishing = data.get("phishing", False)
            
            # Сразу вызываем callback — сервер отвечает синхронно
            
            await result_callback(user_id, is_phishing)
            
        except Exception as e:
            print(f"Ошибка проверки URL {clean_url}: {e}")
            await result_callback(user_id, None)  # None = ошибка

    
    
    async def start(self):
        pass  # ничего не нужно запускать
