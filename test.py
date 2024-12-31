# from TikTok.TikTokApi import TikTokApi


# import asyncio

# async def main():
#     async with TikTokApi() as api:
#         await api.create_sessions(num_sessions=1, 
#                                     sleep_after=5,
#                                     headless=False,
#                                     override_browser_args=["--disable-blink-features=AutomationControlled"],
#                                     starting_url="https://www.tiktok.com/@tiltocacto0o"
#             )
#         tag =  api.hashtag(name="pane2k")
#         hashtag_data = await tag.info()

#         videoCount = hashtag_data['challengeInfo']['statsV2']['videoCount']
#         viewCount  = hashtag_data['challengeInfo']['statsV2']['viewCount']

#         print(f"videoCount = {videoCount}, viewCount = {viewCount}")

#         # video = api.video(id='7330000615835192596')
#         # video_data = await video.info()
#         # print(video_data.as_dict)



#         # print(hashtag_data['challengeInfo']['statsV2'])
    


# if __name__ == "__main__":
#     asyncio.run(main())


import asyncio
import time

async def fetch_data(delay):
    print(f"Начинаю загрузку данных... ({delay} сек.)")
    await asyncio.sleep(delay)  # имитация долгой операции
    print(f"Данные загружены ({delay} сек.)")
    return f"Результат для задержки {delay} сек."

async def main():
    print("Начинаю основную программу")

    # Запускаем несколько асинхронных задач параллельно
    task1 = asyncio.create_task(fetch_data(2))
    task2 = asyncio.create_task(fetch_data(1))

    print("Работаю дальше, пока данные загружаются...")

    # Делаем что-то полезное, пока корутины работают
    for i in range(10):
      time.sleep(0.5)
      print(f"Выполнение основной программы {i}")

    # Ожидаем завершения асинхронных задач
    result1 = await task1
    result2 = await task2

    print(f"Получены результаты: {result1}, {result2}")
    print("Основная программа завершена")

if __name__ == "__main__":
    asyncio.run(main())