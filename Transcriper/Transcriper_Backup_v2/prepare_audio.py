import gradio as gr
import subprocess
import os
import webbrowser
import time

# ==========================================
# الإعدادات
# ==========================================
OUTPUT_FOLDER = "converted_audio"
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

AI_STUDIO_URL = "https://aistudio.google.com/"

# البرومبت المقترح لإرساله مع الملف
TRANSCRIPTION_PROMPT = """
أريد منك تفريغ هذا الملف الصوتي إلى نص ولا تفوت حرف واحد مع مراعاة الآتي:

إزالة التوقيتات

جعل كلام المتن المشروح مائلًا وخط الشرح عادي

إذا سأل الشارح سؤالًا فأجاب أحد الطلاب فاذكر الفقرة في هذه الهيئة:
"الشيخ: السؤال.
طالب: الإجابة.
الشيخ: ...
إلى آخر الفقرة"
ثم ارجع إلى التنسيق الطبيعي عندما ينتهي الشارح من مناقشة الطلبة

تقسيم النص لفقرات حسب المعنى

ضبط التشكيل

ضبط علامات الترقيم (لا تضع نقطة إلا في نهايات الفقرات)

استعمل أقواس القرآن للآيات وأقواس مربعة هكذا [حديث أو قول منقول عن أهل العلم] للأحاديث وأقوال أهل العلم

اجعل الأنواع أو التقسيم في الهيئة الآتية:
وهو نوعان:
أحدهما:.....
والآخر:.....
مع مراعاة أن عدد الأقسام قد يزيد عن 2 (أي: المقصود طريقة التنسيق لا الألفاظ المستخدمة ولا عدد الأقسام)


"""

def convert_to_mp3(input_file):
    if input_file is None:
        return None, "يرجى اختيار ملف أولاً.", ""

    file_name = os.path.basename(input_file.name)
    base_name = os.path.splitext(file_name)[0]
    output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}_optimized.mp3")

    # استخدام ffmpeg لتحويل الملف بجودة مثالية للتفريغ (64kbps, mono) لتصغير الحجم
    # -y للموافقة التلقائية على الاستبدال
    # -vn لحذف الفيديو
    # -ac 1 للتحويل لمونو (أحادي) لتصغير الحجم
    # -b:a 64k جودة كافية جداً للصوت البشري
    cmd = [
        'ffmpeg', '-y', '-i', input_file.name,
        '-vn', '-ac', '1', '-b:a', '64k',
        output_path
    ]

    try:
        print(f"جاري تحويل {file_name}...")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # إظهار تنبيه في الواجهة
        gr.Info("✅ (folder) تم تحويل الملف بنجاح! تم التنزيل وفتح المجلد.")
        time.sleep(5)

        
        # تشغيل مراقب الحافظة (Mode 2) تلقائياً في نافذة جديدة
        python_path = r"C:\Users\saif_\AppData\Local\Programs\Python\Python312\python.exe"
        formatter_script = os.path.join(os.path.dirname(__file__), "ai_studio_formatter.py")
        subprocess.Popen(["cmd", "/c", "start", python_path, formatter_script], shell=True)
        
        # فتح مجلد المخرجات تلقائياً ليسهل سحب الملف
        os.startfile(os.path.abspath(OUTPUT_FOLDER))
        
        # انتظار بسيط لرؤية التنبيه ثم فتح المتصفح
        time.sleep(2)
        webbrowser.open(AI_STUDIO_URL)
        
        message = "✅ تم التحويل بنجاح! تم التنزيل وفتح المجلد وفتح Google AI Studio."
        return output_path, message, TRANSCRIPTION_PROMPT
    except Exception as e:
        return None, f"❌ حدث خطأ أثناء التحويل: {str(e)}", ""

# بناء واجهة Gradio
with gr.Blocks(title="Transcriper - Audio Optimizer") as demo:
    gr.Markdown("""# 🎙️ مجهز الملفات الصوتية للتفريغ
    قم برفع ملف الفيديو أو الصوت هنا لتحويله إلى MP3 مضغوط ومثالي لـ Google AI Studio.""")
    
    with gr.Row():
        with gr.Column():
            input_media = gr.File(label="ارفع ملف (mp4, mkv, m4a, wav, etc.)")
            convert_btn = gr.Button("تحويل وفتح AI Studio", variant="primary")
        
        with gr.Column():
            output_audio = gr.Audio(label="الملف الناتج (MP3)", type="filepath")
            status_msg = gr.Textbox(label="الحالة")
            prompt_box = gr.Textbox(label="البرومبت", interactive=False)
            copy_btn = gr.Button("📋 نسخ البرومبت لاستخدامه في AI Studio", variant="secondary")

    # وظيفة النسخ باستخدام JavaScript
    copy_js = "(v) => { navigator.clipboard.writeText(v); alert('✅ تم نسخ البرومبت إلى الحافظة!'); return v; }"

    convert_btn.click(
        fn=convert_to_mp3,
        inputs=input_media,
        outputs=[output_audio, status_msg, prompt_box]
    )
    
    copy_btn.click(
        fn=None,
        inputs=prompt_box,
        js=copy_js
    )
    
    gr.Markdown("""---
    ### 💡 الخطوات التالية:
    1. ارفع ملفك واضغط تحويل.
    2. سيفتح المتصفح تلقائياً على Google AI Studio.
    3. قم برفع الملف الناتج (المضغوط) هناك.
    4. انسخ البرومبت الموجود في المربع أعلاه والصقه في AI Studio.
    5. بعد انتهاء التفريغ، استخدم 'AI Studio Formatter' لتنسيق النص النهائي في وورد.""")

if __name__ == "__main__":
    demo.launch(inbrowser=True)
