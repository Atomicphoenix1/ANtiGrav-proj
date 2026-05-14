/**
 * AI Studio Pro Scraper (Bookmarklet)
 * ----------------------------------
 * انسخ هذا الكود بالكامل، ثم أنشئ علامة مرجعية (Bookmark) جديدة في متصفحك،
 * وضع هذا الكود في خانة الرابط (URL) مسبوقاً بكلمة javascript:
 * 
 * وظيفة السكربت:
 * 1. استخراج النص من آخر رسالة للذكاء الاصطناعي.
 * 2. الحفاظ على الكلمات المائلة (italics) ووضعها بين علامتي *.
 * 3. دمج الأسطر المكسورة في النص العربي تلقائياً.
 * 4. نسخ النتيجة النهائية للحافظة لتكون جاهزة للمشاريع السابقة.
 */

(function(){
    // 1. العثور على آخر رسالة
    const modelMessages = document.querySelectorAll('.chat-turn-container.model');
    if(!modelMessages.length){
        alert('لم يتم العثور على رسالة من الذكاء الاصطناعي في هذه الصفحة.');
        return;
    }
    const lastMsg = modelMessages[modelMessages.length-1];
    
    // 2. دالة استخراج النص مع الحفاظ على التنسيق
    function cleanText(node){
        let text = "";
        node.childNodes.forEach(child => {
            if(child.nodeType === 3){ // نص
                text += child.textContent;
            } else if(child.tagName === 'BR'){
                text += "\n";
            } else if(['I','EM'].includes(child.tagName) || child.style.fontStyle === 'italic' || window.getComputedStyle(child).fontStyle === 'italic'){
                text += "*" + cleanText(child) + "*";
            } else if(['P','DIV','LI'].includes(child.tagName)){
                text += "\n" + cleanText(child) + "\n";
            } else {
                text += cleanText(child);
            }
        });
        return text;
    }

    let raw = cleanText(lastMsg);
    
    // 3. معالجة انكسار الأسطر (Heal Lines)
    // دمج الأسطر التي لا تنتهي بعلامة ترقيم ختامية
    let lines = raw.split('\n').map(l => l.trim()).filter(l => l !== "");
    let healed = "";
    for(let i=0; i<lines.length; i++){
        healed += lines[i];
        if(i < lines.length - 1){
            let lastChar = lines[i].slice(-1);
            // علامات الترقيم التي نعتبرها نهاية فقرة أو فكرة
            if(['.','!','؟',':','﴾',']',')'].includes(lastChar)){
                healed += "\n\n";
            } else {
                healed += " ";
            }
        }
    }
    
    // 4. النسخ للحافظة
    const el = document.createElement('textarea');
    el.value = healed;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    
    // 5. تنبيه مرئي
    const toast = document.createElement('div');
    toast.style = "position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#1a73e8;color:white;padding:15px 25px;border-radius:30px;z-index:99999;direction:rtl;font-family:sans-serif;box-shadow:0 4px 15px rgba(0,0,0,0.2);font-weight:bold;";
    toast.innerHTML = "تم نسخ النص وتصحيح انكسار الأسطر بنجاح! ✅<br><small style='font-weight:normal;opacity:0.8'>تم الحفاظ على التنسيق المائل ودمج الكلمات المقطوعة.</small>";
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.transition = "opacity 0.5s";
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 500);
    }, 4000);
})();
