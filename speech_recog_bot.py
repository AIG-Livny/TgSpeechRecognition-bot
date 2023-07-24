import telebot
from telebot import types,util
import speech_recognition as sr
from pydub import AudioSegment
from telebot import apihelper
import os
import sys
from pydub.silence import split_on_silence

whitelist = None
if os.path.isfile('./whitelist.py'):
    from whitelist import whitelist

# Bot uses API https://github.com/tdlib/telegram-bot-api
# for processing files up to 4 Gb

apihelper.API_URL = "http://localhost:8081/bot{0}/{1}"

bot = telebot.TeleBot(sys.argv[1])

def convert(mes : telebot.types.Message):
    # Ignore public VM leser than 10 seconds
    if mes.chat.type != "private":
        if mes.voice.duration < 10:
            return
        
    file_info = None
    if mes.content_type == 'voice':
        file_info = bot.get_file(mes.voice.file_id)
    if mes.content_type == 'audio':
        file_info = bot.get_file(mes.audio.file_id)
    if file_info == None:
        return
    
    without_ext = os.path.splitext(file_info.file_path)[0]
   
    audio = AudioSegment.from_file(file_info.file_path)
    r = sr.Recognizer()
    n = len(audio)


    def get_text_from_chunk(filePath):
        audioFile = sr.AudioFile(filePath)
        with audioFile as source:
            r.adjust_for_ambient_noise(source)
            audio   = r.record(source)
            
            # You can change recognition engine here
            return r.recognize_google(audio, language='ru')

    # If VM longer than 50 secs
    if n > 50000:
        chunks_num = round((n/50000)+0.5)
        chunk_len = n//chunks_num
        first_message_id = None

        into_file = False
        if chunks_num > 5:
            into_file = True
            if mes.from_user.language_code == 'ru':
                first_message_text = f'{ os.path.basename(file_info.file_path)}: большой файл. Будет расшифрован и отправлен в виде файла, подождите... '
            else:
                first_message_text = f'{ os.path.basename(file_info.file_path)}: big file. It will be recognized and sended as text file, please wait... '
            first_message_id = bot.send_message(mes.chat.id, first_message_text).id

        whole_text = ''
        warn = False
        for chunk_n in range(0,chunks_num):
            bot.send_chat_action(mes.chat.id, 'typing')
            wfn = f'{without_ext}_{chunk_n}.wav'
            if chunk_n == (chunks_num - 1):
                #last chunk
                chunk : AudioSegment = audio[ chunk_n * chunk_len : len(audio)-1]
            else:
                chunk : AudioSegment = audio[ chunk_n * chunk_len : (chunk_n + 1) * chunk_len]
            
            chunk.export(wfn,format='wav')
            try:
                text = get_text_from_chunk(wfn)
            except:
                if mes.from_user.language_code == 'ru':
                    text = '#!Часть аудио нераспознана!#'
                else:
                    text = '#!Part not recognized!#'
                warn = True
                
            os.remove(wfn)

            if into_file:
                if mes.from_user.language_code == 'ru':
                    new_text = first_message_text + f'Завершено:{round((chunk_n/(chunks_num-1))*100)}%'
                else: 
                    new_text = first_message_text + f'Done:{round((chunk_n/(chunks_num-1))*100)}%' 
                if new_text != whole_text: 
                    bot.edit_message_text(chat_id=mes.chat.id, text=new_text, message_id=first_message_id)
                    whole_text = new_text
                with open(without_ext+'.txt', 'a+') as f:
                    f.write(text)
            else:
                whole_text += text
                if chunk_n == 0:
                    first_message_id = bot.send_message(mes.chat.id, text, reply_to_message_id=mes.id).id
                else:
                    bot.edit_message_text(chat_id=mes.chat.id, text=whole_text, message_id=first_message_id)
                    if chunk_n == (chunks_num - 1):
                        if warn:
                            if mes.from_user.language_code == 'ru':
                                bot.send_message(mes.chat.id, f'{ os.path.basename(file_info.file_path)}: Расшифровка завершена с ошибками, возможно из-за сильного шума или слишком тихого голоса')
                            else:
                                bot.send_message(mes.chat.id, f'{ os.path.basename(file_info.file_path)}: Recognition completed with errors, possibly due to loud noise or too quiet voice')
                        else:
                            if mes.from_user.language_code == 'ru':
                                bot.send_message(mes.chat.id, f'{ os.path.basename(file_info.file_path)}: Расшифровка завершена!')
                            else:
                                bot.send_message(mes.chat.id, f'{ os.path.basename(file_info.file_path)}: Recognition completed!')


        if into_file:
            f = open(without_ext+'.txt',"rb")
            bot.send_document(mes.chat.id,f)
            f.close()
            os.remove(without_ext+'.txt')
            if warn:
                if mes.from_user.language_code == 'ru':
                    bot.send_message(mes.chat.id, f'{ os.path.basename(file_info.file_path)}: Расшифровка завершена с ошибками, возможно из-за сильного шума или слишком тихого голоса')
                else:
                    bot.send_message(mes.chat.id, f'{ os.path.basename(file_info.file_path)}: Recognition completed with errors, possibly due to loud noise or too quiet voice')
    else:
        # If VM shorter than 50 secs
        wfn = without_ext + '.wav'
        audio.export(wfn, format='wav')
        try:
            text = get_text_from_chunk(wfn)
            os.remove(wfn)
        except:
            return
        bot.send_message(mes.chat.id, text, reply_to_message_id=mes.id)
        
@bot.message_handler(content_types=['audio'])
def get_audio(mes : telebot.types.Message):
    if mes.chat.type == "private":
        if whitelist and mes.from_user.id not in whitelist:
            return
        convert(mes)

@bot.message_handler(content_types=['voice'])
def get_voice(mes : telebot.types.Message):
    if mes.chat.type == "private":
        if whitelist and mes.from_user.id not in whitelist:
            return
        convert(mes)
        
# Start bot
bot.infinity_polling(allowed_updates=util.update_types)