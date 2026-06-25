// --- Cosmic Alchemist App Logic (Standard sequential loading) ---

// --- Translation Dictionary ---
const TRANSLATIONS = {
  en: {
    logoTitle: "THE COSMIC VAULT",
    logoSubtitle: "Where wisdom drifts through time",
    streakLabel: "DAYS",
    addQuoteBtn: "Add Quote",
    vaultManagerBtn: "Vault Manager",
    sectionLabel: "CURRENT ORBIT FOCUS",
    emptyTitle: "The Vault is Quiet",
    emptyDesc: "Write your first memory into the scroll to begin your reflections.",
    addFirstQuoteBtn: "Add First Quote",
    cycleQuoteBtn: "Next Cycle",
    editQuoteBtn: "Edit",
    syncN8nBtn: "Sync to n8n",
    impressionsLabel: "Impressions",
    createdLabel: "First Opened",
    lastSeenLabel: "Last Seen",
    timelineTitle: "Reflection Chronicles",
    emptyTimeline: "No reflections recorded for this wisdom yet. Write down your first thought or realization below.",
    timestampLabel: "Auto-timestamped",
    recordBtn: "Record Thought",
    formLabelText: "The Wisdom (Quote Text)",
    formLabelAuthor: "Author / Source",
    formLabelTags: "Category Tags (Comma Separated)",
    formHelpTags: "Separate categories with commas. They will turn into glowing interactive pills.",
    cancelBtn: "Cancel",
    saveIntoVaultBtn: "Save into Vault",
    vaultTitle: "The Archive Vault",
    settingsTitle: "Cosmic Integrations (n8n)",
    settingsDesc: "Connect your cosmic vault to an external n8n workflow. Once connected, you can click \"Sync to n8n\" on any quote to instantly trigger your automated pipelines.",
    settingsLabelUrl: "n8n Webhook URL",
    settingsPayloadLabel: "JSON Payload Schema sent to n8n:",
    settingsTestBtn: "Test Connection",
    settingsSaveBtn: "Save Integration",
    audioLabel: "Ambient Pad",
    
    // Dynamic / JavaScript Alerts and Labels
    never: "Never",
    justNow: "Just now",
    reflectionsSuffix: "Reflection",
    reflectionsSuffixPlural: "Reflections",
    confirmDeleteReflection: "Are you sure you want to purge this memory reflection?",
    confirmDeleteQuote: "Are you sure you want to permanently erase this quote from the archive?",
    transcribeNew: "Transcribe New Quote",
    editWisdom: "Transcribe Wisdom",
    quotesSaved: "quotes saved in the cosmos",
    quotesFiltered: "quotes filtered from space",
    noMatches: "No matches found in your cosmic memory vault. Try broadening your searches.",
    webhookConfigAlert: "Please configure your n8n Webhook URL in the Settings menu (top right) before syncing.",
    syncSuccess: "Synced!",
    syncingText: "Syncing...",
    testSuccess: "Test success! n8n responded with a positive signal.",
    testFailed: "Connection failed: ",
    streakAlert: "🔥 Cosmic Flame of Reflection!\nYou have visited your vault for {count} consecutive day{plural}. Keep returning daily to solidify your memories!",
    streakDayPlural: "s",
    streakDaySingular: "",
    urlAlert: "Please provide a valid HTTP/HTTPS Webhook URL.",
    audioPlaying: "Playing Zen",
    placeholders: {
      reflectionInput: "Type a reflection, realization, or update on how you have applied this quote...",
      formQuoteText: "Type the quote or thought that inspired you...",
      formQuoteAuthor: "e.g. Marcus Aurelius, Unknown, The Matrix",
      formQuoteTags: "e.g. Philosophy, Coding, Life, Growth",
      vaultSearch: "Fuzzy search text, authors, reflections...",
      settingsUrl: "https://primary-production.n8n.cloud/webhook/..."
    },
    titles: {
      streakBtn: "View Reflection Streak",
      languageBtn: "Toggle Language / تغيير اللغة",
      settingsBtn: "n8n Integration",
      cycleBtn: "Cycle to Another Quote",
      editBtn: "Edit this Quote",
      syncBtn: "Sync to n8n Webhook",
      soundToggle: "Toggle Ambient Audio"
    }
  },
  ar: {
    // ── Display text: uses full tashkeel so Aref Ruqaa Ink & Amiri render beautifully ──
    logoTitle: "ٱلْقَبْوُ ٱلْكَوْنِيّ",
    logoSubtitle: "حَيْثُ تَتَلَاقَى الْحِكْمَةُ عَبْرَ مَدَارَاتِ الزَّمَن",
    streakLabel: "أيام",
    addQuoteBtn: "إضافة حكمة",
    vaultManagerBtn: "أرشيف الحكمة",
    sectionLabel: "مَدَارُ التَّرْكِيزِ الحَالِي",
    emptyTitle: "ٱلْمَدَارُ هَادِئٌ تَمَامًا",
    emptyDesc: "دَوِّنْ أُولَى حِكَمِكَ وَتَأَمُّلَاتِكَ لِتَبْدَأَ دَوْرَتَكَ الفِكْرِيَّةَ الكَوْنِيَّة.",
    addFirstQuoteBtn: "إضافة أوّل حكمة",
    cycleQuoteBtn: "المدار التالي",
    editQuoteBtn: "تعديل",
    syncN8nBtn: "مزامنة مع n8n",
    impressionsLabel: "مَرَّاتُ القِرَاءَة",
    createdLabel: "تاريخ التدوين",
    lastSeenLabel: "آخر مدار",
    timelineTitle: "سِجِلُّ التَّأَمُّلَاتِ",
    emptyTimeline: "لَا تُوجَدُ تَأَمُّلَاتٌ مُسَجَّلَةٌ لِهَذِهِ الحِكْمَةِ بَعْد. سَجِّلْ أَوَّلَ خَاطِرَةٍ أَوْ إِدْرَاكٍ فِيمَا يَلِي.",
    timestampLabel: "تَوْقِيتٌ فَلَكِيٌّ تِلْقَائِيّ",
    recordBtn: "تدوين التأمل",
    formLabelText: "الحِكْمَة (نَصُّ الِاقْتِبَاس)",
    formLabelAuthor: "القائل / المصدر",
    formLabelTags: "تصنيفات الحكمة (مفصولة بفاصلة)",
    formHelpTags: "افصل بين التصنيفات بفاصلة. ستتحوّل إلى كبسولات نيون متوهّجة.",
    cancelBtn: "إلغاء",
    saveIntoVaultBtn: "حفظ في الأرشيف",
    vaultTitle: "أَرْشِيفُ الحِكْمَةِ الكَوْنِيّ",
    settingsTitle: "تَكَامُلُ الأَنْظِمَة (n8n)",
    settingsDesc: "اِرْبِطْ قَبْوَكَ الكَوْنِيَّ بِنِظَامِ n8n الخَارِجِيّ. بِمُجَرَّدِ الاِتِّصَال، يُمْكِنُكَ المَزَامَنَةُ الفَوْرِيَّةُ لِإِرْسَالِ بَيَانَاتِكَ لِشَبَكَاتِكَ وَتَطْبِيقَاتِكَ الخَاصَّة.",
    settingsLabelUrl: "رابط webhook لـ n8n",
    settingsPayloadLabel: "هيكل حزمة JSON المرسلة إلى n8n:",
    settingsTestBtn: "اختبار الاتصال",
    settingsSaveBtn: "حفظ الإعدادات",
    audioLabel: "اللَّحْنُ الهَادِئ",
    
    // Dynamic / JavaScript Alerts and Labels
    never: "أبداً",
    justNow: "الآن",
    reflectionsSuffix: "تأمُّل",
    reflectionsSuffixPlural: "تأمُّلات",
    confirmDeleteReflection: "هل أنت متأكّد من رغبتك في مسح هذا التأمّل من ذاكرتك الكونيّة؟",
    confirmDeleteQuote: "هَلْ أَنْتَ مُتَأَكِّدٌ مِنْ رَغْبَتِكَ فِي حَذْفِ هَذِهِ الحِكْمَةِ نِهَائِيًّا مِنَ الأَرْشِيف؟",
    transcribeNew: "تَدْوِينُ حِكْمَةٍ جَدِيدَة",
    editWisdom: "تَعْدِيلُ حِكْمَةِ الأَرْشِيف",
    quotesSaved: "حِكْمَةٌ مَحْفُوظَةٌ فِي الفَضَاءِ الكَوْنِيّ",
    quotesFiltered: "حِكْمَةٌ مُصَفَّاةٌ مِنَ الفَضَاء",
    noMatches: "لَمْ يُعْثَرْ عَلَى نَتَائِجَ فِي قَبْوِ الذَّاكِرَةِ الكَوْنِيَّة. جَرِّبْ تَغْيِيرَ كَلِمَاتِ البَحْث.",
    webhookConfigAlert: "يُرْجَى تَهْيِئَةُ رَابِطِ Webhook الخَاصِّ بِـ n8n فِي قَائِمَةِ الإِعْدَادَاتِ قَبْلَ البَدْءِ بِالمُزَامَنَة.",
    syncSuccess: "تَمَّتِ المُزَامَنَة!",
    syncingText: "جَارِي المُزَامَنَة...",
    testSuccess: "نَجَحَ الاِخْتِبَار! اسْتَجَابَ نِظَامُ n8n بِنَجَاح.",
    testFailed: "فَشَلَ الاِتِّصَال: ",
    streakAlert: "🔥 شُعْلَةُ التَّأَمُّلِ الكَوْنِيَّة!\nلَقَدْ زُرْتَ قَبْوَكَ الفِكْرِيَّ لِمُدَّةِ {count} {plural} مُتَتَالِيَة. وَاظِبْ عَلَى الحُضُورِ يَوْمِيًّا لِتَرْسِيخِ شُعْلَةِ الذَّاكِرَة!",
    streakDayPlural: "أَيَّام",
    streakDaySingular: "يَوْم",
    urlAlert: "يُرْجَى تَقْدِيمُ رَابِطِ Webhook صَحِيحٍ يَبْدَأُ بِـ HTTP/HTTPS.",
    audioPlaying: "وَضْعُ التَّأَمُّل",
    placeholders: {
      reflectionInput: "اُكْتُبْ تَأَمُّلًا أَوْ فِكْرَةً أَوْ دَرْسًا حَيَاتِيًّا اسْتَخْلَصْتَهُ مِنْ تَطْبِيقِ هَذِهِ الحِكْمَة...",
      formQuoteText: "اُكْتُبْ الحِكْمَةَ أَوِ الفِكْرَةَ المُلْهِمَةَ هُنَا...",
      formQuoteAuthor: "مِثَال: مَارْكُوس أُورِيلِيُوس، اِبْنُ سِينَا، غَانْدِي",
      formQuoteTags: "مِثَال: فَلْسَفَة، بَرْمَجَة، حَيَاة، تَطْوِير",
      vaultSearch: "بَحْثٌ فَلَكِيٌّ بِالنُّصُوصِ وَالقَائِلِينَ وَالتَّأَمُّلَات...",
      settingsUrl: "https://primary-production.n8n.cloud/webhook/..."
    },
    titles: {
      streakBtn: "عَرْضُ شُعْلَةِ الذَّاكِرَةِ الكَوْنِيَّة",
      languageBtn: "Toggle Language / تَغْيِيرُ اللُّغَة",
      settingsBtn: "تَكَامُلُ أَنْظِمَةِ n8n",
      cycleBtn: "العُبُورُ لِمَدَارِ حِكْمَةٍ أُخْرَى",
      editBtn: "تَعْدِيلُ هَذِهِ الحِكْمَة",
      syncBtn: "مُزَامَنَةُ البَيَانَاتِ مَعَ webhook n8n",
      soundToggle: "تَشْغِيل/إِيقَافُ اللَّحْنِ الكَوْنِيّ"
    }
  }
};

// --- State Management ---
const STATE_KEYS = {
  LANGUAGE: 'cosmic_vault_language',
  SETTINGS: 'cosmic_vault_settings' // shared globally
};

let state = {
  language: 'en', // 'en' or 'ar'
  quotes: [],     // localized
  activeQuoteId: null,
  settings: {
    webhookUrl: ''
  },
  streak: {
    count: 0,
    lastVisit: '' // YYYY-MM-DD
  }
};

// --- DOM References ---
const els = {
  focusQuoteCard: document.getElementById('focus-quote-card'),
  emptyFocusState: document.getElementById('empty-focus-state'),
  focusQuoteContent: document.getElementById('focus-quote-content'),
  displayQuoteText: document.getElementById('display-quote-text'),
  displayQuoteAuthor: document.getElementById('display-quote-author'),
  displayQuoteTags: document.getElementById('display-quote-tags'),
  
  cycleQuoteBtn: document.getElementById('cycle-quote-btn'),
  editFocusBtn: document.getElementById('edit-focus-btn'),
  syncN8nBtn: document.getElementById('sync-n8n-btn'),
  
  focusInsights: document.getElementById('focus-insights'),
  statImpressions: document.getElementById('stat-impressions'),
  statCreated: document.getElementById('stat-created'),
  statLastSeen: document.getElementById('stat-last-seen'),
  
  reflectionCount: document.getElementById('reflection-count'),
  reflectionTimeline: document.getElementById('reflection-timeline'),
  emptyTimelineState: document.getElementById('empty-timeline-state'),
  reflectionComposer: document.getElementById('reflection-composer'),
  reflectionInput: document.getElementById('reflection-input'),
  saveReflectionBtn: document.getElementById('save-reflection-btn'),
  
  // Drawers and Modals
  addDrawerOverlay: document.getElementById('add-drawer-overlay'),
  addDrawer: document.getElementById('add-drawer'),
  openAddDrawerBtn: document.getElementById('open-add-drawer-btn'),
  closeAddDrawerBtn: document.getElementById('close-add-drawer-btn'),
  cancelAddDrawerBtn: document.getElementById('cancel-add-drawer-btn'),
  emptyAddBtn: document.getElementById('empty-add-btn'),
  
  quoteForm: document.getElementById('quote-form'),
  formQuoteId: document.getElementById('form-quote-id'),
  formQuoteText: document.getElementById('form-quote-text'),
  formQuoteAuthor: document.getElementById('form-quote-author'),
  formQuoteTags: document.getElementById('form-quote-tags'),
  drawerTitle: document.getElementById('drawer-title'),
  
  vaultDrawerOverlay: document.getElementById('vault-drawer-overlay'),
  vaultDrawer: document.getElementById('vault-drawer'),
  openVaultBtn: document.getElementById('open-vault-btn'),
  closeVaultBtn: document.getElementById('close-vault-btn'),
  vaultSearchInput: document.getElementById('vault-search-input'),
  vaultTagFilters: document.getElementById('vault-tag-filters'),
  archiveCountText: document.getElementById('archive-count-text'),
  archiveList: document.getElementById('archive-list'),
  
  settingsModalOverlay: document.getElementById('settings-modal-overlay'),
  openSettingsBtn: document.getElementById('open-settings-btn'),
  closeSettingsBtn: document.getElementById('close-settings-btn'),
  settingsWebhookUrl: document.getElementById('settings-webhook-url'),
  testWebhookBtn: document.getElementById('test-webhook-btn'),
  saveSettingsBtn: document.getElementById('save-settings-btn'),
  
  streakCountDisplay: document.getElementById('streak-count-display'),
  streakEmberBtn: document.getElementById('streak-ember-btn'),
  
  languageToggleBtn: document.getElementById('language-toggle-btn'),
  langToggleText: document.getElementById('lang-toggle-text'),
  
  soundToggle: document.getElementById('sound-toggle'),
  ambientAudio: document.getElementById('ambient-audio')
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  // 1. Read initial language (English by default, or loaded from LocalStorage)
  state.language = localStorage.getItem(STATE_KEYS.LANGUAGE) || 'en';
  
  // 2. Setup language environment (direction, translations)
  applyLanguageConfiguration();

  // 3. Start canvas background animation
  initStarfield();
  
  // 4. Bind UI listeners
  bindEventListeners();
  
  // 5. Choose initial focus quote
  cycleToNextQuote(true);
  
  // 6. Render lucide icons
  lucide.createIcons();
});

// --- Localization Core Engine ---
function applyLanguageConfiguration() {
  const lang = state.language;
  const t = TRANSLATIONS[lang];

  // A. Set document attributes
  document.documentElement.lang = lang;
  document.body.dir = lang === 'ar' ? 'rtl' : 'ltr';
  
  // B. Toggle button text (shows the OPPOSITE language choice)
  els.langToggleText.textContent = lang === 'en' ? 'AR' : 'EN';

  // C. Translate elements with [data-i18n]
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) {
      // If it contains a lucide icon, preserve the icon and translate only the text span
      const textSpan = el.querySelector('span');
      if (textSpan) {
        textSpan.textContent = t[key];
      } else {
        // If there's an icon but no inner span (e.g. headers inside widgets), only replace trailing text or replace innerHTML safely
        const icon = el.querySelector('i');
        if (icon) {
          el.innerHTML = '';
          el.appendChild(icon);
          const space = document.createTextNode(' ' + t[key]);
          el.appendChild(space);
        } else {
          el.textContent = t[key];
        }
      }
    }
  });

  // D. Update inputs placeholders
  els.reflectionInput.placeholder = t.placeholders.reflectionInput;
  els.formQuoteText.placeholder = t.placeholders.formQuoteText;
  els.formQuoteAuthor.placeholder = t.placeholders.formQuoteAuthor;
  els.formQuoteTags.placeholder = t.placeholders.formQuoteTags;
  els.vaultSearchInput.placeholder = t.placeholders.vaultSearch;
  els.settingsWebhookUrl.placeholder = t.placeholders.settingsUrl;

  // E. Update UI Titles/Tooltips
  els.streakEmberBtn.title = t.titles.streakBtn;
  els.languageToggleBtn.title = t.titles.languageBtn;
  els.openSettingsBtn.title = t.titles.settingsBtn;
  els.cycleQuoteBtn.title = t.titles.cycleBtn;
  els.editFocusBtn.title = t.titles.editBtn;
  els.syncN8nBtn.title = t.titles.syncBtn;
  els.soundToggle.title = t.titles.soundToggle;

  // F. Load localized databases from storage
  loadLocalizedLocalStorage();

  // G. Update visit streaks (runs independently for each language)
  checkAndUpdateStreak();
}

function switchLanguage() {
  state.language = state.language === 'en' ? 'ar' : 'en';
  localStorage.setItem(STATE_KEYS.LANGUAGE, state.language);
  
  // Clean active quote focus
  state.activeQuoteId = null;

  // Re-apply language translations & load relative data
  applyLanguageConfiguration();

  // Cycle to load the active localized quote
  cycleToNextQuote(true);
  
  // Re-render UI elements
  renderFocusQuote();
  renderVaultList();
  lucide.createIcons();
}

// --- LocalStorage localized Helpers ---
function loadLocalizedLocalStorage() {
  const lang = state.language;
  const quoteKey = `cosmic_vault_quotes_${lang}`;
  const streakKey = `cosmic_vault_streak_${lang}`;

  try {
    state.quotes = JSON.parse(localStorage.getItem(quoteKey)) || [];
    state.streak = JSON.parse(localStorage.getItem(streakKey)) || { count: 0, lastVisit: '' };
    state.settings = JSON.parse(localStorage.getItem(STATE_KEYS.SETTINGS)) || { webhookUrl: '' };
  } catch (e) {
    console.error('Could not load localized databases', e);
  }
}

function saveQuotes() {
  const lang = state.language;
  localStorage.setItem(`cosmic_vault_quotes_${lang}`, JSON.stringify(state.quotes));
}

function saveStreak() {
  const lang = state.language;
  localStorage.setItem(`cosmic_vault_streak_${lang}`, JSON.stringify(state.streak));
}

function saveSettings() {
  localStorage.setItem(STATE_KEYS.SETTINGS, JSON.stringify(state.settings));
}

// --- Localized Visit Streak Engine ---
function checkAndUpdateStreak() {
  const today = getLocalDateString(new Date());
  const lastVisit = state.streak.lastVisit;

  if (!lastVisit) {
    state.streak.count = 1;
    state.streak.lastVisit = today;
  } else if (lastVisit === today) {
    // Already checked in today
  } else {
    const lastVisitDate = new Date(lastVisit);
    const todayDate = new Date(today);
    const diffTime = Math.abs(todayDate - lastVisitDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      state.streak.count += 1;
      state.streak.lastVisit = today;
    } else {
      state.streak.count = 1;
      state.streak.lastVisit = today;
    }
  }

  saveStreak();
  
  // Format numbers in English script for layout consistency
  els.streakCountDisplay.textContent = state.streak.count;
}

function getLocalDateString(date) {
  const offset = date.getTimezoneOffset();
  const adjustedDate = new Date(date.getTime() - (offset * 60 * 1000));
  return adjustedDate.toISOString().split('T')[0];
}

// --- Smart Quote Cycling Algorithm ---
function cycleToNextQuote(isInitial = false) {
  if (state.quotes.length === 0) {
    state.activeQuoteId = null;
    renderFocusQuote();
    return;
  }

  let nextQuote;
  
  if (state.quotes.length === 1) {
    nextQuote = state.quotes[0];
  } else {
    const sortedCandidates = [...state.quotes].sort((a, b) => {
      if ((a.impressions || 0) !== (b.impressions || 0)) {
        return (a.impressions || 0) - (b.impressions || 0);
      }
      const timeA = a.lastSeen ? new Date(a.lastSeen).getTime() : 0;
      const timeB = b.lastSeen ? new Date(b.lastSeen).getTime() : 0;
      return timeA - timeB;
    });

    if (state.activeQuoteId && sortedCandidates[0].id === state.activeQuoteId) {
      nextQuote = sortedCandidates[1];
    } else {
      nextQuote = sortedCandidates[0];
    }
  }

  if (nextQuote) {
    state.activeQuoteId = nextQuote.id;
    nextQuote.impressions = (nextQuote.impressions || 0) + 1;
    nextQuote.lastSeen = new Date().toISOString();
    saveQuotes();
    
    if (!isInitial) {
      els.focusQuoteCard.style.opacity = '0';
      els.focusQuoteCard.style.transform = 'scale(0.97)';
      setTimeout(() => {
        renderFocusQuote();
        els.focusQuoteCard.style.opacity = '1';
        els.focusQuoteCard.style.transform = 'scale(1)';
      }, 300);
    } else {
      renderFocusQuote();
    }
  }
}

// --- View Rendering ---
function renderFocusQuote() {
  const t = TRANSLATIONS[state.language];

  if (!state.activeQuoteId || state.quotes.length === 0) {
    els.emptyFocusState.classList.remove('hidden');
    els.focusQuoteContent.classList.add('hidden');
    els.focusInsights.classList.add('hidden');
    els.reflectionComposer.classList.add('hidden');
    els.reflectionTimeline.innerHTML = '';
    els.emptyTimelineState.classList.remove('hidden');
    els.reflectionCount.textContent = `0 ${t.reflectionsSuffixPlural}`;
    return;
  }

  const quote = state.quotes.find(q => q.id === state.activeQuoteId);
  if (!quote) return;

  els.emptyFocusState.classList.add('hidden');
  els.focusQuoteContent.classList.remove('hidden');
  els.focusInsights.classList.remove('hidden');
  els.reflectionComposer.classList.remove('hidden');

  els.displayQuoteText.textContent = quote.text;
  els.displayQuoteAuthor.textContent = quote.author || (state.language === 'en' ? 'Unknown' : 'مجهول');
  
  // Render Tags
  els.displayQuoteTags.innerHTML = '';
  if (quote.tags && quote.tags.length > 0) {
    quote.tags.forEach(tagText => {
      const tagSpan = document.createElement('span');
      tagSpan.className = 'tag';
      tagSpan.textContent = tagText;
      tagSpan.addEventListener('click', () => {
        openVaultDrawer(tagText);
      });
      els.displayQuoteTags.appendChild(tagSpan);
    });
  }

  // Render Insight Stats
  els.statImpressions.textContent = quote.impressions || 1;
  els.statCreated.textContent = new Date(quote.created).toLocaleDateString(state.language, { month: 'short', day: 'numeric', year: '2-digit' });
  els.statLastSeen.textContent = quote.lastSeen 
    ? new Date(quote.lastSeen).toLocaleTimeString(state.language, { hour: '2-digit', minute: '2-digit' }) 
    : t.justNow;

  // Render Reflections Timeline
  renderReflectionTimeline(quote);
}

function renderReflectionTimeline(quote) {
  els.reflectionTimeline.innerHTML = '';
  const reflections = quote.reflections || [];
  const t = TRANSLATIONS[state.language];
  
  const countSuffix = reflections.length === 1 ? t.reflectionsSuffix : t.reflectionsSuffixPlural;
  els.reflectionCount.textContent = `${reflections.length} ${countSuffix}`;

  if (reflections.length === 0) {
    els.emptyTimelineState.classList.remove('hidden');
    return;
  }

  els.emptyTimelineState.classList.add('hidden');
  
  const sortedReflections = [...reflections].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  sortedReflections.forEach((reflection, index) => {
    const card = document.createElement('div');
    card.className = 'reflection-card';
    
    const originalIndex = reflections.findIndex(r => r.timestamp === reflection.timestamp && r.text === reflection.text);

    const formattedDate = new Date(reflection.timestamp).toLocaleString(state.language, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    card.innerHTML = `
      <div class="timeline-dot"></div>
      <div class="reflection-content">
        <div class="reflection-meta">
          <span class="reflection-time">${formattedDate}</span>
          <button class="reflection-delete-btn" data-index="${originalIndex}" title="${state.language === 'en' ? 'Delete reflection' : 'حذف التأمل'}">
            <i data-lucide="trash-2"></i>
          </button>
        </div>
        <p class="reflection-text">${escapeHTML(reflection.text)}</p>
      </div>
    `;

    card.querySelector('.reflection-delete-btn').addEventListener('click', () => {
      deleteReflection(quote.id, originalIndex);
    });

    els.reflectionTimeline.appendChild(card);
  });

  lucide.createIcons();
}

function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}

// --- Reflection Actions ---
function addReflection() {
  const text = els.reflectionInput.value.trim();
  if (!text || !state.activeQuoteId) return;

  const quote = state.quotes.find(q => q.id === state.activeQuoteId);
  if (!quote) return;

  if (!quote.reflections) quote.reflections = [];
  
  quote.reflections.push({
    timestamp: new Date().toISOString(),
    text: text
  });

  saveQuotes();
  els.reflectionInput.value = '';
  renderFocusQuote();
}

function deleteReflection(quoteId, reflectionIndex) {
  const t = TRANSLATIONS[state.language];
  if (!confirm(t.confirmDeleteReflection)) return;
  
  const quote = state.quotes.find(q => q.id === quoteId);
  if (!quote || !quote.reflections) return;

  quote.reflections.splice(reflectionIndex, 1);
  saveQuotes();
  renderFocusQuote();
}

// --- Quote Creation Drawer ---
function openAddQuoteDrawer(quoteId = null) {
  const t = TRANSLATIONS[state.language];
  
  if (quoteId) {
    const quote = state.quotes.find(q => q.id === quoteId);
    if (!quote) return;

    els.drawerTitle.innerHTML = `<i data-lucide="edit-3"></i> ${t.editWisdom}`;
    els.formQuoteId.value = quote.id;
    els.formQuoteText.value = quote.text;
    els.formQuoteAuthor.value = quote.author || '';
    els.formQuoteTags.value = (quote.tags || []).join(', ');
  } else {
    els.drawerTitle.innerHTML = `<i data-lucide="sparkles"></i> ${t.transcribeNew}`;
    els.formQuoteId.value = '';
    els.quoteForm.reset();
  }

  els.addDrawerOverlay.classList.add('active');
  lucide.createIcons();
}

function closeAddQuoteDrawer() {
  els.addDrawerOverlay.classList.remove('active');
}

function handleQuoteSubmit(e) {
  e.preventDefault();
  
  const quoteId = els.formQuoteId.value;
  const text = els.formQuoteText.value.trim();
  const author = els.formQuoteAuthor.value.trim() || (state.language === 'en' ? 'Unknown' : 'مجهول');
  
  const tagsString = els.formQuoteTags.value;
  const tags = tagsString
    ? tagsString.split(',').map(t => t.trim()).filter(t => t.length > 0)
    : [];

  if (quoteId) {
    const quote = state.quotes.find(q => q.id === quoteId);
    if (quote) {
      quote.text = text;
      quote.author = author;
      quote.tags = tags;
    }
  } else {
    const newQuote = {
      id: 'q_' + Date.now(),
      text: text,
      author: author,
      tags: tags,
      impressions: 0,
      created: new Date().toISOString(),
      lastSeen: null,
      reflections: []
    };
    state.quotes.push(newQuote);
    state.activeQuoteId = newQuote.id;
  }

  saveQuotes();
  closeAddQuoteDrawer();
  renderFocusQuote();
}

function deleteQuote(quoteId) {
  const t = TRANSLATIONS[state.language];
  if (!confirm(t.confirmDeleteQuote)) return;

  state.quotes = state.quotes.filter(q => q.id !== quoteId);
  saveQuotes();

  if (state.activeQuoteId === quoteId) {
    state.activeQuoteId = state.quotes.length > 0 ? state.quotes[0].id : null;
  }

  renderFocusQuote();
  renderVaultList();
}

// --- Vault Archive Manager Drawer ---
let currentTagFilter = null;

function openVaultDrawer(initialTagFilter = null) {
  currentTagFilter = initialTagFilter;
  els.vaultSearchInput.value = '';
  els.vaultDrawerOverlay.classList.add('active');
  renderVaultList();
}

function closeVaultDrawer() {
  els.vaultDrawerOverlay.classList.remove('active');
}

function renderVaultList() {
  const searchQuery = els.vaultSearchInput.value.trim().toLowerCase();
  const t = TRANSLATIONS[state.language];
  
  // Get unique tags
  const allTags = new Set();
  state.quotes.forEach(q => {
    if (q.tags) q.tags.forEach(t => allTags.add(t));
  });

  els.vaultTagFilters.innerHTML = '';
  
  // "All" tag
  const allPill = document.createElement('span');
  allPill.className = `filter-tag ${!currentTagFilter ? 'active' : ''}`;
  allPill.textContent = state.language === 'en' ? 'ALL' : 'الكل';
  allPill.addEventListener('click', () => {
    currentTagFilter = null;
    renderVaultList();
  });
  els.vaultTagFilters.appendChild(allPill);

  allTags.forEach(tag => {
    const pill = document.createElement('span');
    pill.className = `filter-tag ${currentTagFilter === tag ? 'active' : ''}`;
    pill.textContent = tag.toUpperCase();
    pill.addEventListener('click', () => {
      currentTagFilter = (currentTagFilter === tag) ? null : tag;
      renderVaultList();
    });
    els.vaultTagFilters.appendChild(pill);
  });

  // Filter list
  const filteredQuotes = state.quotes.filter(q => {
    if (currentTagFilter && (!q.tags || !q.tags.includes(currentTagFilter))) {
      return false;
    }
    
    if (searchQuery) {
      const matchText = q.text.toLowerCase().includes(searchQuery);
      const matchAuthor = q.author.toLowerCase().includes(searchQuery);
      const matchTags = q.tags ? q.tags.some(t => t.toLowerCase().includes(searchQuery)) : false;
      const matchReflections = q.reflections ? q.reflections.some(r => r.text.toLowerCase().includes(searchQuery)) : false;
      
      return matchText || matchAuthor || matchTags || matchReflections;
    }
    return true;
  });

  els.archiveCountText.textContent = `${filteredQuotes.length} ${t.quotesFiltered}`;

  els.archiveList.innerHTML = '';
  
  if (filteredQuotes.length === 0) {
    els.archiveList.innerHTML = `
      <div class="empty-timeline-state">
        <p>${t.noMatches}</p>
      </div>
    `;
    return;
  }

  filteredQuotes.forEach(quote => {
    const activeClass = quote.id === state.activeQuoteId ? 'active' : '';
    
    const card = document.createElement('div');
    card.className = `archive-card ${activeClass}`;
    
    card.innerHTML = `
      <p class="archive-card-text">${escapeHTML(quote.text)}</p>
      <div class="archive-card-meta">
        <span class="archive-card-author">— ${escapeHTML(quote.author)}</span>
        <div class="archive-card-actions">
          <button class="archive-action-btn edit" data-id="${quote.id}" title="${state.language === 'en' ? 'Edit' : 'تعديل'}">
            <i data-lucide="edit-3"></i>
          </button>
          <button class="archive-action-btn delete" data-id="${quote.id}" title="${state.language === 'en' ? 'Delete' : 'حذف'}">
            <i data-lucide="trash-2"></i>
          </button>
        </div>
      </div>
    `;

    card.addEventListener('click', (e) => {
      if (e.target.closest('.archive-action-btn')) return;
      state.activeQuoteId = quote.id;
      saveQuotes();
      renderFocusQuote();
      closeVaultDrawer();
    });

    card.querySelector('.archive-action-btn.edit').addEventListener('click', (e) => {
      e.stopPropagation();
      openAddQuoteDrawer(quote.id);
    });

    card.querySelector('.archive-action-btn.delete').addEventListener('click', (e) => {
      e.stopPropagation();
      deleteQuote(quote.id);
    });

    els.archiveList.appendChild(card);
  });

  lucide.createIcons();
}

// --- Integrations & n8n Webhook Sync ---
function openSettingsModal() {
  els.settingsWebhookUrl.value = state.settings.webhookUrl || '';
  els.settingsModalOverlay.classList.add('active');
}

function closeSettingsModal() {
  els.settingsModalOverlay.classList.remove('active');
}

function handleSaveSettings() {
  const url = els.settingsWebhookUrl.value.trim();
  const t = TRANSLATIONS[state.language];

  if (url && !isValidUrl(url)) {
    alert(t.urlAlert);
    return;
  }
  
  state.settings.webhookUrl = url;
  saveSettings();
  closeSettingsModal();
}

function isValidUrl(str) {
  try {
    new URL(str);
    return true;
  } catch (_) {
    return false;
  }
}

async function triggerN8nWebhook(manualQuoteId = null) {
  const t = TRANSLATIONS[state.language];
  const targetId = manualQuoteId || state.activeQuoteId;
  
  if (!targetId) {
    alert(state.language === 'en' ? 'Please add a quote first.' : 'يرجى إضافة حكمة أولاً للبدء.');
    return;
  }

  const quote = state.quotes.find(q => q.id === targetId);
  if (!quote) return;

  const url = state.settings.webhookUrl;
  if (!url) {
    alert(t.webhookConfigAlert);
    openSettingsModal();
    return;
  }

  const btn = els.syncN8nBtn;
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader" class="spin-slow"></i> <span>${t.syncingText}</span>`;
  lucide.createIcons();

  const payload = {
    event: 'manual_sync',
    language: state.language,
    timestamp: new Date().toISOString(),
    quote: {
      id: quote.id,
      text: quote.text,
      author: quote.author,
      tags: quote.tags || [],
      impressions: quote.impressions || 1,
      streak: state.streak.count,
      reflections: quote.reflections || []
    }
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      btn.innerHTML = `<i data-lucide="check-circle-2" style="color: var(--neon-emerald)"></i> <span style="color: var(--neon-emerald)">${t.syncSuccess}</span>`;
      lucide.createIcons();
      setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        lucide.createIcons();
      }, 3000);
    } else {
      throw new Error(`Server returned HTTP ${response.status}`);
    }
  } catch (err) {
    console.error('Webhook sync failed', err);
    alert(`${t.testFailed}${err.message}`);
    btn.disabled = false;
    btn.innerHTML = originalHtml;
    lucide.createIcons();
  }
}

async function testWebhookConnection() {
  const t = TRANSLATIONS[state.language];
  const url = els.settingsWebhookUrl.value.trim();
  if (!url || !isValidUrl(url)) {
    alert(state.language === 'en' ? 'Please enter a valid webhook URL' : 'يرجى تقديم رابط webhook صحيح');
    return;
  }

  const btn = els.testWebhookBtn;
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = state.language === 'en' ? 'Testing...' : 'جاري الاختبار...';

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        event: 'test_connection',
        language: state.language,
        timestamp: new Date().toISOString(),
        message: 'Hello from the Multilingual Cosmic Vault Dashboard!'
      })
    });

    if (response.ok) {
      alert(t.testSuccess);
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (err) {
    alert(`${t.testFailed}${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

// --- Audio Control Panel ---
function toggleAmbientAudio() {
  const audio = els.ambientAudio;
  const bubble = els.soundToggle;
  const text = bubble.querySelector('.bubble-text');
  const t = TRANSLATIONS[state.language];

  if (audio.paused) {
    audio.play().then(() => {
      bubble.classList.add('playing');
      text.textContent = t.audioPlaying;
    }).catch(e => {
      console.warn('Audio auto-play failed', e);
    });
  } else {
    audio.pause();
    bubble.classList.remove('playing');
    text.textContent = t.audioLabel;
  }
}

// --- Event Bindings ---
function bindEventListeners() {
  // Quote cycling
  els.cycleQuoteBtn.addEventListener('click', () => cycleToNextQuote(false));
  
  // Reflections
  els.saveReflectionBtn.addEventListener('click', addReflection);
  els.reflectionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      addReflection();
    }
  });

  // Language toggling
  els.languageToggleBtn.addEventListener('click', switchLanguage);

  // Add/Edit drawers
  els.openAddDrawerBtn.addEventListener('click', () => openAddQuoteDrawer());
  els.emptyAddBtn.addEventListener('click', () => openAddQuoteDrawer());
  els.closeAddDrawerBtn.addEventListener('click', closeAddQuoteDrawer);
  els.cancelAddDrawerBtn.addEventListener('click', closeAddQuoteDrawer);
  els.quoteForm.addEventListener('submit', handleQuoteSubmit);
  
  // Focus Quote actions
  els.editFocusBtn.addEventListener('click', () => {
    if (state.activeQuoteId) {
      openAddQuoteDrawer(state.activeQuoteId);
    }
  });
  els.syncN8nBtn.addEventListener('click', () => triggerN8nWebhook());

  // Archive Explorer Sidebar
  els.openVaultBtn.addEventListener('click', () => openVaultDrawer());
  els.closeVaultBtn.addEventListener('click', closeVaultDrawer);
  els.vaultSearchInput.addEventListener('input', renderVaultList);

  // Settings Modals
  els.openSettingsBtn.addEventListener('click', openSettingsModal);
  els.closeSettingsBtn.addEventListener('click', closeSettingsModal);
  els.saveSettingsBtn.addEventListener('click', handleSaveSettings);
  els.testWebhookBtn.addEventListener('click', testWebhookConnection);

  // Streak ember trigger
  els.streakEmberBtn.addEventListener('click', () => {
    const t = TRANSLATIONS[state.language];
    const plural = state.streak.count === 1 ? t.streakDaySingular : t.streakDayPlural;
    const alertMsg = t.streakAlert
      .replace('{count}', state.streak.count)
      .replace('{plural}', plural);
    alert(alertMsg);
  });

  // Sound panel trigger
  els.soundToggle.addEventListener('click', toggleAmbientAudio);

  // Close Drawers/Modals on overlay click
  els.addDrawerOverlay.addEventListener('click', (e) => {
    if (e.target === els.addDrawerOverlay) closeAddQuoteDrawer();
  });
  els.vaultDrawerOverlay.addEventListener('click', (e) => {
    if (e.target === els.vaultDrawerOverlay) closeVaultDrawer();
  });
  els.settingsModalOverlay.addEventListener('click', (e) => {
    if (e.target === els.settingsModalOverlay) closeSettingsModal();
  });
}
