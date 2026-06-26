// Smart English Trainer - Core Application Logic (Flask + SQLite API version)

// App State
let currentMode = "sentence"; // "sentence", "toeic" (Part 5), or "toeic-part2" (Part 2)
let units = [];
let currentSentences = [];
let activeUnitId = null;
let currentSentenceIndex = 0;

// TOEIC Part 5 Mode State
let toeicQuestions = [];
let currentToeicIndex = 0;
let totalToeicCount = 0;
let isToeicAnswered = false;
let isConfiguringApiKey = false;
let currentCategory = "all"; // "all", "grammar", "vocabulary"

// TOEIC Part 2 Mode State
let toeicPart2Questions = [];
let currentPart2Index = 0;
let totalPart2Count = 0;
let isPart2Answered = false;
let currentFilter = "all"; // "all", "new", "review", "mastered"

// UI Settings
let isScrambleMode = false;
let isAnswerShowing = false;
let autoSpeak = true;
let correctSpeak = true;
let selectedVoiceName = "";
let speechRate = 1.0;

// Pet Egg Growth State
let petState = {
  level: 1,
  exp: 0,
  streak: 0,
  lastFedDate: "",
  skin: "default",
  inventory: {
    snack: 0,
    toy: 0,
    charm: 0
  },
  daily: {
    date: "",
    correct: 0,
    sentence: 0,
    part2: 0,
    claimed: []
  }
};
let sentenceRewardGiven = false;
let petAnimationFrame = 1;
let petSaveTimer = null;

const PET_SKINS = [
  { id: "default", name: "Shell", icon: "🥚", unlockLevel: 1 },
  { id: "aqua", name: "Aqua", icon: "💧", unlockLevel: 3 },
  { id: "ember", name: "Ember", icon: "🔥", unlockLevel: 6 },
  { id: "blossom", name: "Bloom", icon: "🌸", unlockLevel: 9 },
  { id: "cosmic", name: "Cosmic", icon: "✨", unlockLevel: 12 }
];

const PET_ITEMS = {
  snack: { name: "Snack", icon: "🍪", exp: 25 },
  toy: { name: "Toy", icon: "🧸", exp: 15, streak: 1 },
  charm: { name: "Charm", icon: "💎", exp: 60 }
};

const PET_DAILY_QUESTS = [
  { id: "correct3", label: "Correct 3", target: 3, field: "correct", exp: 25, item: "snack" },
  { id: "sentence2", label: "Sentence 2", target: 2, field: "sentence", exp: 20, item: "toy" },
  { id: "part2_2", label: "Listening 2", target: 2, field: "part2", exp: 30, item: "charm" }
];

const PET_MAX_STAGE = 20;
const PET_GROWTH_STAGES = [
  { level: 1, key: "stage-01", name: "Tiny Egg", subtitle: "A quiet beginning. Answer correctly to warm it up." },
  { level: 2, key: "stage-02", name: "Warm Egg", subtitle: "The shell is glowing after your early practice." },
  { level: 3, key: "stage-03", name: "Hairline Crack", subtitle: "A small crack appears. Something is listening." },
  { level: 4, key: "stage-04", name: "Bright Crack", subtitle: "The crack grows brighter with each correct answer." },
  { level: 5, key: "stage-05", name: "Peekaboo", subtitle: "A tiny face peeks out from the shell." },
  { level: 6, key: "stage-06", name: "Half Hatched", subtitle: "It is almost ready to join your lessons." },
  { level: 7, key: "stage-07", name: "New Hatchling", subtitle: "Your study companion has hatched." },
  { level: 8, key: "stage-08", name: "Steady Hatchling", subtitle: "It stands more confidently now." },
  { level: 9, key: "stage-09", name: "Soft Feathers", subtitle: "Small feathers start to shine." },
  { level: 10, key: "stage-10", name: "First Star", subtitle: "A first star mark celebrates your consistency." },
  { level: 11, key: "stage-11", name: "Young Companion", subtitle: "It is bigger, brighter, and ready for longer practice." },
  { level: 12, key: "stage-12", name: "Clear Voice", subtitle: "Its energy responds to listening practice." },
  { level: 13, key: "stage-13", name: "Little Cape", subtitle: "A small learning cape appears." },
  { level: 14, key: "stage-14", name: "Cape Upgrade", subtitle: "The cape glows as your streaks improve." },
  { level: 15, key: "stage-15", name: "Mature Companion", subtitle: "A major growth milestone is unlocked." },
  { level: 16, key: "stage-16", name: "Bright Aura", subtitle: "Its aura strengthens with daily effort." },
  { level: 17, key: "stage-17", name: "Star Crest", subtitle: "A crest marks advanced progress." },
  { level: 18, key: "stage-18", name: "Wide Wings", subtitle: "The wings grow wider and more stable." },
  { level: 19, key: "stage-19", name: "Starlit Aura", subtitle: "Stars gather around your companion." },
  { level: 20, key: "stage-20", name: "Final Evolution", subtitle: "The full evolution is complete. Keep training to power it up." }
];

// DOM Elements
const tabSentence = document.getElementById("tab-sentence");
const tabToeic = document.getElementById("tab-toeic");
const tabToeicPart2 = document.getElementById("tab-toeic-part2");
const unitSelector = document.getElementById("unit-selector");
const toeicFilter = document.getElementById("toeic-filter");
const toeicCategoryFilter = document.getElementById("toeic-category-filter");
const progressIndicator = document.getElementById("progress-indicator");
const progressBarFill = document.getElementById("progress-bar-fill");
const clockDisplay = document.getElementById("clock-display");
const modeScrambleToggle = document.getElementById("mode-scramble-toggle");
const btnBack = document.getElementById("btn-back");
const btnReset = document.getElementById("btn-reset");
const btnSpeak = document.getElementById("btn-speak");
const btnImport = document.getElementById("btn-import");
const btnTtsSettings = document.getElementById("btn-tts-settings");

const btnMarkMastered = document.getElementById("btn-mark-mastered");
const btnMarkReview = document.getElementById("btn-mark-review");
const chinesePrompt = document.getElementById("chinese-prompt");
const englishAnswer = document.getElementById("english-answer");
const answerHint = document.getElementById("answer-hint");

// Spelling & Scramble Zones
const spellingZone = document.getElementById("spelling-zone");
const scrambleZone = document.getElementById("scramble-zone");
const scrambleSlots = document.getElementById("scramble-slots");
const scrambleOptions = document.getElementById("scramble-options");
const sentenceModeToggle = document.getElementById("sentence-mode-toggle");
const sentenceAiPanel = document.getElementById("sentence-ai-panel");
const btnSentenceExplain = document.getElementById("btn-sentence-explain");
const sentenceExplainBtnText = document.getElementById("sentence-explain-btn-text");
const sentenceAiResult = document.getElementById("sentence-ai-result");
const sentenceAiContent = document.getElementById("sentence-ai-content");
const wordLookupInput = document.getElementById("word-lookup-input");
const btnWordLookup = document.getElementById("btn-word-lookup");
const wordNoteResult = document.getElementById("word-note-result");
const wordNoteContent = document.getElementById("word-note-content");

// TOEIC Part 5 Zone Elements
const toeicZone = document.getElementById("toeic-zone");
const toeicQuestionText = document.getElementById("toeic-question-text");
const toeicOptButtons = document.querySelectorAll("#toeic-zone .toeic-opt-btn");
const btnToeicExplain = document.getElementById("btn-toeic-explain");
const explainBtnText = document.getElementById("explain-btn-text");
const explanationBox = document.getElementById("explanation-box");
const toeicExplanation = document.getElementById("toeic-explanation");

// TOEIC Part 2 Zone Elements
const toeicPart2Zone = document.getElementById("toeic-part2-zone");
const btnPart2Play = document.getElementById("btn-part2-play");
const audioPart2Player = document.getElementById("audio-part2-player");
const toeicPart2StatusText = document.getElementById("toeic-part2-status-text");
const part2QuestionReveal = document.getElementById("part2-question-reveal");
const toeicPart2QuestionText = document.getElementById("toeic-part2-question-text");
const part2TranscriptA = document.getElementById("part2-transcript-a");
const part2TranscriptB = document.getElementById("part2-transcript-b");
const part2TranscriptC = document.getElementById("part2-transcript-c");
const toeicPart2OptButtons = document.querySelectorAll(".toeic-part2-opt-btn");
const btnPart2Explain = document.getElementById("btn-part2-explain");
const part2ExplainBtnText = document.getElementById("part2-explain-btn-text");
const part2ExplanationBox = document.getElementById("part2-explanation-box");
const toeicPart2Explanation = document.getElementById("toeic-part2-explanation");

// Modals
const importModal = document.getElementById("import-modal");
const voiceModal = document.getElementById("voice-modal");
const modalClose = document.getElementById("modal-close");
const voiceModalClose = document.getElementById("voice-modal-close");
const btnImportCancel = document.getElementById("btn-import-cancel");
const btnImportSubmit = document.getElementById("btn-import-submit");
const btnVoiceClose = document.getElementById("btn-voice-close");

const importTextarea = document.getElementById("import-textarea");
const importUnitName = document.getElementById("import-unit-name");
const voiceSelect = document.getElementById("voice-select");
const voiceSpeed = document.getElementById("voice-speed");
const speedVal = document.getElementById("speed-val");
const autoSpeakToggle = document.getElementById("auto-speak-toggle");
const correctSpeakToggle = document.getElementById("correct-speak-toggle");
const geminiKeyInput = document.getElementById("gemini-key-input");
const geminiModelSelect = document.getElementById("gemini-model-select");
const petEgg = document.getElementById("pet-egg");
const petEggImg = document.getElementById("pet-egg-img");
const petStageName = document.getElementById("pet-stage-name");
const petLevel = document.getElementById("pet-level");
const petExpFill = document.getElementById("pet-exp-fill");
const petExpText = document.getElementById("pet-exp-text");
const petCarePanel = document.getElementById("pet-care-panel");
const petAvatar = document.getElementById("pet-avatar");
const petAvatarImg = document.getElementById("pet-avatar-img");
const petAvatarSpark = document.getElementById("pet-avatar-spark");
const petCareTitle = document.getElementById("pet-care-title");
const petCareSubtitle = document.getElementById("pet-care-subtitle");
const petSkinList = document.getElementById("pet-skin-list");
const petItemList = document.getElementById("pet-item-list");
const petDailyList = document.getElementById("pet-daily-list");

// Structure to hold current sentence processed words
let processedWords = []; 
let scrambleSelections = []; // Holds index of selected options in scramble mode

/* ----------------- Initialization ----------------- */

async function init() {
  // 1. Load configuration settings from LocalStorage (UI states)
  loadSettingsFromLocalStorage();
  await loadPetState();
  renderPet();
  setInterval(() => {
    petAnimationFrame = petAnimationFrame >= 3 ? 1 : petAnimationFrame + 1;
    updatePetImages();
  }, 500);

  // 2. Setup Clock
  updateClock();
  setInterval(updateClock, 60000);

  // 3. Setup Speech Voices
  setupSpeechVoices();
  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = setupSpeechVoices;
  }

  // 4. Register Event Listeners
  registerEventListeners();

  // 5. Load data depending on current tab
  switchTab(currentMode);
}

// Update Local Clock Display
function updateClock() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  clockDisplay.textContent = `${hours}:${minutes}`;
}

// Set up voices dropdown
function setupSpeechVoices() {
  const voices = window.speechSynthesis.getVoices();
  const englishVoices = voices.filter(v => v.lang.startsWith("en-") || v.lang.startsWith("en_"));
  
  voiceSelect.innerHTML = "";
  
  if (englishVoices.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "無可用英文語音 (系統預設)";
    voiceSelect.appendChild(opt);
    return;
  }

  englishVoices.forEach(voice => {
    const option = document.createElement("option");
    option.value = voice.name;
    const label = `${voice.name} (${voice.lang})`;
    option.textContent = label;
    if (voice.name === selectedVoiceName) {
      option.selected = true;
    }
    voiceSelect.appendChild(option);
  });

  if (!selectedVoiceName && englishVoices.length > 0) {
    selectedVoiceName = englishVoices[0].name;
  }
}

/* ----------------- Settings LocalStorage & Config API ----------------- */

function loadSettingsFromLocalStorage() {
  try {
    const storedVoiceName = localStorage.getItem("selected_voice_name");
    if (storedVoiceName) {
      selectedVoiceName = storedVoiceName;
    }

    const storedSpeed = localStorage.getItem("speech_rate");
    if (storedSpeed) {
      speechRate = parseFloat(storedSpeed);
      voiceSpeed.value = speechRate;
      speedVal.textContent = speechRate.toFixed(1);
    }

    const storedAutoSpeak = localStorage.getItem("auto_speak");
    if (storedAutoSpeak !== null) {
      autoSpeak = JSON.parse(storedAutoSpeak);
      autoSpeakToggle.checked = autoSpeak;
    }

    const storedCorrectSpeak = localStorage.getItem("correct_speak");
    if (storedCorrectSpeak !== null) {
      correctSpeak = JSON.parse(storedCorrectSpeak);
      correctSpeakToggle.checked = correctSpeak;
    }

    // Restore last active positions
    const storedUnitId = localStorage.getItem("active_unit_id");
    if (storedUnitId) {
      activeUnitId = parseInt(storedUnitId, 10);
    }

    const storedSentenceIdx = localStorage.getItem("active_sentence_index");
    if (storedSentenceIdx) {
      currentSentenceIndex = parseInt(storedSentenceIdx, 10);
    }

    const storedMode = localStorage.getItem("current_mode");
    if (storedMode) {
      currentMode = storedMode;
    }

    const storedToeicIdx = localStorage.getItem("current_toeic_index");
    if (storedToeicIdx) {
      currentToeicIndex = parseInt(storedToeicIdx, 10);
    }

    const storedPart2Idx = localStorage.getItem("current_part2_index");
    if (storedPart2Idx) {
      currentPart2Index = parseInt(storedPart2Idx, 10);
    }
  } catch (e) {
    console.error("Error loading settings", e);
  }
}

function saveSettingsToLocalStorage() {
  try {
    localStorage.setItem("selected_voice_name", selectedVoiceName);
    localStorage.setItem("speech_rate", speechRate);
    localStorage.setItem("auto_speak", autoSpeak);
    localStorage.setItem("correct_speak", correctSpeak);
    localStorage.setItem("current_mode", currentMode);
    localStorage.setItem("current_toeic_index", currentToeicIndex);
    localStorage.setItem("current_part2_index", currentPart2Index);
    if (activeUnitId) localStorage.setItem("active_unit_id", activeUnitId);
    localStorage.setItem("active_sentence_index", currentSentenceIndex);
  } catch (e) {
    console.error("Error saving settings", e);
  }
}

/* ----------------- Pet Egg Growth ----------------- */

function getTodayKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getPetExpToNextLevel(level = petState.level) {
  if (level <= 5) return 35 + (level * 5);
  if (level <= 10) return 60 + (level * 8);
  if (level <= 15) return 95 + (level * 10);
  return 140 + (level * 12);
}

function getPetStage(level = petState.level) {
  const cappedLevel = Math.max(1, Math.min(level, PET_MAX_STAGE));
  return PET_GROWTH_STAGES[cappedLevel - 1];
}

function getPetFramePath(skinId, stageKey, frame = petAnimationFrame) {
  return `assets/pets/skins/${skinId}/${stageKey}/frame-${frame}.png`;
}

function getDefaultPetState() {
  return {
    level: 1,
    exp: 0,
    streak: 0,
    lastFedDate: "",
    skin: "default",
    inventory: {
      snack: 0,
      toy: 0,
      charm: 0
    },
    daily: {
      date: getTodayKey(),
      correct: 0,
      sentence: 0,
      part2: 0,
      claimed: []
    }
  };
}

function normalizePetState(rawPet) {
  const defaults = getDefaultPetState();
  const rawInventory = rawPet && typeof rawPet.inventory === "object" ? rawPet.inventory : {};
  const rawDaily = rawPet && typeof rawPet.daily === "object" ? rawPet.daily : {};

  return {
    level: Number.isFinite(rawPet && rawPet.level) ? rawPet.level : defaults.level,
    exp: Number.isFinite(rawPet && rawPet.exp) ? rawPet.exp : defaults.exp,
    streak: Number.isFinite(rawPet && rawPet.streak) ? rawPet.streak : defaults.streak,
    lastFedDate: typeof (rawPet && rawPet.lastFedDate) === "string" ? rawPet.lastFedDate : defaults.lastFedDate,
    skin: typeof (rawPet && rawPet.skin) === "string" ? rawPet.skin : defaults.skin,
    inventory: {
      snack: Number.isFinite(rawInventory.snack) ? rawInventory.snack : 0,
      toy: Number.isFinite(rawInventory.toy) ? rawInventory.toy : 0,
      charm: Number.isFinite(rawInventory.charm) ? rawInventory.charm : 0
    },
    daily: {
      date: typeof rawDaily.date === "string" ? rawDaily.date : defaults.daily.date,
      correct: Number.isFinite(rawDaily.correct) ? rawDaily.correct : 0,
      sentence: Number.isFinite(rawDaily.sentence) ? rawDaily.sentence : 0,
      part2: Number.isFinite(rawDaily.part2) ? rawDaily.part2 : 0,
      claimed: Array.isArray(rawDaily.claimed) ? rawDaily.claimed : []
    }
  };
}

function ensurePetDailyState() {
  const today = getTodayKey();
  if (!petState.daily || petState.daily.date !== today) {
    petState.daily = {
      date: today,
      correct: 0,
      sentence: 0,
      part2: 0,
      claimed: []
    };
    savePetState();
  }
}

function addPetExp(amount) {
  petState.exp += amount;
  while (petState.exp >= getPetExpToNextLevel()) {
    petState.exp -= getPetExpToNextLevel();
    petState.level += 1;
  }
}

function getActiveSkin() {
  return PET_SKINS.find(skin => skin.id === petState.skin) || PET_SKINS[0];
}

function isPetStateEmpty(state) {
  if (!state) return true;
  const inventory = state.inventory || {};
  const daily = state.daily || {};
  const hasItems = Object.values(inventory).some(count => count > 0);
  const hasDailyProgress = (daily.correct || 0) > 0 || (daily.sentence || 0) > 0 || (daily.part2 || 0) > 0 || (daily.claimed || []).length > 0;
  return (
    state.level === 1 &&
    state.exp === 0 &&
    state.streak === 0 &&
    !state.lastFedDate &&
    (!state.skin || state.skin === "default") &&
    !hasItems &&
    !hasDailyProgress
  );
}

function loadPetStateFromLocalStorage() {
  const storedPet = localStorage.getItem("pet_egg_state");
  if (!storedPet) {
    return getDefaultPetState();
  }
  return normalizePetState(JSON.parse(storedPet));
}

async function loadPetState() {
  let localPetState = null;
  try {
    localPetState = loadPetStateFromLocalStorage();
    petState = localPetState;
  } catch (e) {
    console.error("Error loading local pet state", e);
    petState = getDefaultPetState();
  }

  try {
    const response = await fetch("/api/pet/state");
    if (response.ok) {
      const result = await response.json();
      if (result.state) {
        const dbPetState = normalizePetState(result.state);
        if (isPetStateEmpty(dbPetState) && !isPetStateEmpty(localPetState)) {
          petState = localPetState;
          schedulePetStateSync();
        } else {
          petState = dbPetState;
        }
      } else {
        schedulePetStateSync();
      }
    }
  } catch (e) {
    console.warn("Pet database sync unavailable; using localStorage fallback.", e);
  }

  ensurePetDailyState();
}

function savePetState() {
  try {
    localStorage.setItem("pet_egg_state", JSON.stringify(petState));
  } catch (e) {
    console.error("Error saving pet state", e);
  }
  schedulePetStateSync();
}

function schedulePetStateSync() {
  clearTimeout(petSaveTimer);
  petSaveTimer = setTimeout(syncPetStateToDatabase, 250);
}

async function syncPetStateToDatabase() {
  try {
    await fetch("/api/pet/state", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state: petState })
    });
  } catch (e) {
    console.warn("Pet database save failed; localStorage copy was kept.", e);
  }
}

function renderPet() {
  if (!petEgg || !petStageName || !petLevel || !petExpFill || !petExpText) return;

  ensurePetDailyState();
  const expToNext = getPetExpToNextLevel();
  const stage = getPetStage();
  const skin = getActiveSkin();
  const expPercent = Math.min(100, Math.round((petState.exp / expToNext) * 100));

  petStageName.textContent = `${stage.name} · ${skin.name}`;
  petLevel.textContent = `Lv.${petState.level}`;
  petExpFill.style.width = `${expPercent}%`;
  petExpText.textContent = `${petState.exp} / ${expToNext} XP · Streak ${petState.streak}`;

  if (petAvatar && petCareTitle && petCareSubtitle) {
    petAvatar.className = `pet-avatar skin-${skin.id}`;
    if (petAvatarSpark) {
      petAvatarSpark.textContent = skin.icon;
    }
    petCareTitle.textContent = `${stage.name} · ${skin.name}`;
    petCareSubtitle.textContent = stage.subtitle;
  }

  updatePetImages();
  renderPetSkins();
  renderPetItems();
  renderPetDailyQuests();
}

function updatePetImages() {
  const stage = getPetStage();
  const skin = getActiveSkin();
  const framePath = getPetFramePath(skin.id, stage.key);

  if (petEggImg) {
    petEggImg.src = framePath;
    petEggImg.alt = "";
  }
  if (petAvatarImg) {
    petAvatarImg.src = framePath;
    petAvatarImg.alt = stage.name;
  }
}

function animatePetGrowth() {
  if (!petEgg) return;
  petEgg.classList.remove("grow");
  void petEgg.offsetWidth;
  petEgg.classList.add("grow");
}

function rewardPet(source = "correct") {
  const today = getTodayKey();
  let gainedExp = 10;

  ensurePetDailyState();
  petState.streak += 1;
  petState.daily.correct += 1;
  if (source === "sentence") {
    petState.daily.sentence += 1;
  }
  if (source === "part2") {
    petState.daily.part2 += 1;
  }

  if (petState.streak > 0 && petState.streak % 3 === 0) {
    gainedExp += 10;
    petState.inventory.snack += 1;
  }
  if (petState.lastFedDate !== today) {
    gainedExp += 30;
    petState.lastFedDate = today;
  }

  addPetExp(gainedExp);

  savePetState();
  renderPet();
  animatePetGrowth();
}

function resetPetStreak() {
  if (petState.streak === 0) return;
  petState.streak = 0;
  savePetState();
  renderPet();
}

function renderPetSkins() {
  if (!petSkinList) return;
  petSkinList.innerHTML = "";

  PET_SKINS.forEach(skin => {
    const unlocked = petState.level >= skin.unlockLevel;
    const button = document.createElement("button");
    button.className = `pet-skin-btn${petState.skin === skin.id ? " active" : ""}`;
    button.dataset.skinId = skin.id;
    button.disabled = !unlocked;
    button.title = unlocked ? skin.name : `Unlocks at Lv.${skin.unlockLevel}`;
    button.innerHTML = `<span>${skin.icon}</span><span>${skin.name}</span>${unlocked ? "" : `<small>Lv.${skin.unlockLevel}</small>`}`;
    petSkinList.appendChild(button);
  });
}

function renderPetItems() {
  if (!petItemList) return;
  petItemList.innerHTML = "";

  Object.entries(PET_ITEMS).forEach(([itemId, item]) => {
    const count = petState.inventory[itemId] || 0;
    const button = document.createElement("button");
    button.className = "pet-item-btn";
    button.dataset.itemId = itemId;
    button.disabled = count <= 0;
    button.title = count > 0 ? `Use ${item.name}` : `No ${item.name} available`;
    button.innerHTML = `<span>${item.icon}</span><span>${item.name}</span><strong>${count}</strong>`;
    petItemList.appendChild(button);
  });
}

function renderPetDailyQuests() {
  if (!petDailyList) return;
  petDailyList.innerHTML = "";

  PET_DAILY_QUESTS.forEach(quest => {
    const progress = Math.min(petState.daily[quest.field] || 0, quest.target);
    const complete = progress >= quest.target;
    const claimed = petState.daily.claimed.includes(quest.id);
    const row = document.createElement("div");
    row.className = `pet-daily-row${complete ? " complete" : ""}${claimed ? " claimed" : ""}`;
    row.innerHTML = `
      <div>
        <span>${quest.label}</span>
        <small>${progress} / ${quest.target} · +${quest.exp} XP · ${PET_ITEMS[quest.item].icon}</small>
      </div>
      <button class="pet-claim-btn" data-quest-id="${quest.id}" ${complete && !claimed ? "" : "disabled"}>
        ${claimed ? "Done" : "Claim"}
      </button>
    `;
    petDailyList.appendChild(row);
  });
}

function selectPetSkin(skinId) {
  const skin = PET_SKINS.find(candidate => candidate.id === skinId);
  if (!skin || petState.level < skin.unlockLevel) return;
  petState.skin = skin.id;
  savePetState();
  renderPet();
}

function usePetItem(itemId) {
  const item = PET_ITEMS[itemId];
  if (!item || (petState.inventory[itemId] || 0) <= 0) return;

  petState.inventory[itemId] -= 1;
  if (item.streak) {
    petState.streak += item.streak;
  }
  addPetExp(item.exp);
  savePetState();
  renderPet();
  animatePetGrowth();
}

function claimPetDailyQuest(questId) {
  ensurePetDailyState();
  const quest = PET_DAILY_QUESTS.find(candidate => candidate.id === questId);
  if (!quest || petState.daily.claimed.includes(quest.id)) return;

  const progress = petState.daily[quest.field] || 0;
  if (progress < quest.target) return;

  petState.daily.claimed.push(quest.id);
  petState.inventory[quest.item] = (petState.inventory[quest.item] || 0) + 1;
  addPetExp(quest.exp);
  savePetState();
  renderPet();
  animatePetGrowth();
}

// Fetch saved Gemini API Key configuration
async function fetchConfigSettings() {
  try {
    const response = await fetch("/api/settings/config");
    const config = await response.json();
    if (config.gemini_api_key_set) {
      geminiKeyInput.placeholder = "金鑰已設定：" + config.gemini_api_key_masked;
    } else {
      geminiKeyInput.placeholder = "請貼上您的 API 金鑰 (多益 AI 解析用)";
      geminiKeyInput.value = "";
    }
    if (geminiModelSelect && config.gemini_model) {
      geminiModelSelect.value = config.gemini_model;
    }
  } catch (e) {
    console.error("Failed to fetch API key status", e);
  }
}

// Save Gemini API key/model
async function saveConfigSettings() {
  const apiKey = geminiKeyInput.value.strip ? geminiKeyInput.value.strip() : geminiKeyInput.value.trim();
  const geminiModel = geminiModelSelect ? geminiModelSelect.value : "gemini-3.1-flash-lite";

  try {
    const response = await fetch("/api/settings/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        gemini_api_key: apiKey,
        gemini_model: geminiModel
      })
    });
    const result = await response.json();
    if (result.success) {
      geminiKeyInput.value = "";
      fetchConfigSettings();
    }
  } catch (e) {
    console.error("Failed to save config key:", e);
  }
}

/* ----------------- Tab Switching ----------------- */

function switchTab(mode) {
  currentMode = mode;
  saveSettingsToLocalStorage();

  // Blur any active inputs to prevent typing issues
  if (document.activeElement) {
    document.activeElement.blur();
  }

  // Reset shared visibility elements so they do not bleed across tabs
  answerHint.classList.add("hidden");
  explanationBox.classList.add("hidden");
  chinesePrompt.classList.add("hidden");
  isAnswerShowing = false;

  const toeicHelps = document.querySelectorAll(".toeic-help-shortcut");

  // Highlight active tab button
  if (mode === "toeic") {
    tabToeic.classList.add("active");
    tabSentence.classList.remove("active");
    tabToeicPart2.classList.remove("active");

    toeicHelps.forEach(el => el.classList.remove("hidden"));

    // Adjust visibility
    unitSelector.classList.add("hidden");
    toeicFilter.classList.remove("hidden");
    toeicCategoryFilter.classList.remove("hidden");
    btnBack.classList.add("hidden");
    btnImport.classList.add("hidden");
    sentenceModeToggle.classList.add("hidden");

    spellingZone.classList.add("hidden");
    scrambleZone.classList.add("hidden");
    toeicZone.classList.remove("hidden");
    toeicPart2Zone.classList.add("hidden");
    sentenceAiPanel.classList.add("hidden");
    
    // Fetch and load toeic questions
    fetchToeicQuestions();
  } else if (mode === "toeic-part2") {
    tabToeicPart2.classList.add("active");
    tabSentence.classList.remove("active");
    tabToeic.classList.remove("active");

    toeicHelps.forEach(el => el.classList.remove("hidden"));

    // Adjust visibility
    unitSelector.classList.add("hidden");
    toeicFilter.classList.remove("hidden");
    toeicCategoryFilter.classList.add("hidden");
    btnBack.classList.add("hidden");
    btnImport.classList.add("hidden");
    sentenceModeToggle.classList.add("hidden");

    spellingZone.classList.add("hidden");
    scrambleZone.classList.add("hidden");
    toeicZone.classList.add("hidden");
    toeicPart2Zone.classList.remove("hidden");
    sentenceAiPanel.classList.add("hidden");

    // Fetch and load toeic part 2 questions
    fetchToeicPart2Questions();
  } else {
    tabSentence.classList.add("active");
    tabToeic.classList.remove("active");
    tabToeicPart2.classList.remove("active");

    toeicHelps.forEach(el => el.classList.add("hidden"));

    // Adjust visibility
    unitSelector.classList.remove("hidden");
    toeicFilter.classList.add("hidden");
    toeicCategoryFilter.classList.add("hidden");
    btnBack.classList.remove("hidden");
    btnImport.classList.remove("hidden");
    sentenceModeToggle.classList.remove("hidden");

    toeicZone.classList.add("hidden");
    toeicPart2Zone.classList.add("hidden");
    sentenceAiPanel.classList.remove("hidden");
    
    // Fetch units and sentences
    fetchUnits();
  }
}

/* ----------------- API Integration: Units & Sentences ----------------- */

async function fetchUnits(selectUnitId = null) {
  try {
    const response = await fetch("/api/units");
    units = await response.json();

    if (units.length === 0) return;

    // Populate Selector Dropdown
    unitSelector.innerHTML = "";
    units.forEach(unit => {
      const option = document.createElement("option");
      option.value = unit.id;
      option.textContent = unit.name;
      unitSelector.appendChild(option);
    });

    if (selectUnitId !== null) {
      activeUnitId = selectUnitId;
    } else if (!activeUnitId || !units.find(u => u.id === activeUnitId)) {
      activeUnitId = units[0].id;
    }

    unitSelector.value = activeUnitId;
    saveSettingsToLocalStorage();

    fetchSentences(activeUnitId);
  } catch (e) {
    console.error("Failed to fetch units:", e);
    alert("無法連接到後端伺服器，請確保 Flask 伺服器正在運行！");
  }
}

async function fetchSentences(unitId) {
  try {
    const response = await fetch(`/api/units/${unitId}/sentences`);
    currentSentences = await response.json();

    if (currentSentences.length === 0) {
      currentSentenceIndex = 0;
      spellingZone.innerHTML = "";
      chinesePrompt.textContent = "請匯入題目";
      englishAnswer.textContent = "";
      progressIndicator.textContent = "0 / 0";
      progressBarFill.style.width = "0%";
      return;
    }

    if (currentSentenceIndex >= currentSentences.length) {
      currentSentenceIndex = 0;
    }

    loadSentence();
  } catch (e) {
    console.error("Failed to fetch sentences:", e);
  }
}

function loadSentence() {
  if (currentSentences.length === 0) return;

  const sentenceData = currentSentences[currentSentenceIndex];
  sentenceRewardGiven = false;
  
  progressIndicator.textContent = `${currentSentenceIndex + 1} / ${currentSentences.length}`;
  
  const percentage = ((currentSentenceIndex + 1) / currentSentences.length) * 100;
  progressBarFill.style.width = `${percentage}%`;

  chinesePrompt.textContent = sentenceData.chinese;
  chinesePrompt.classList.remove("hidden");
  englishAnswer.textContent = sentenceData.english;
  
  isAnswerShowing = false;
  answerHint.classList.add("hidden");
  explanationBox.classList.add("hidden");
  renderSavedSentenceAiNote(sentenceData);
  clearWordNote();

  // Load Status Tag
  updateStatusTags(sentenceData.status);

  // Parse English sentence into words and punctuation
  const rawWords = sentenceData.english.trim().replace(/\s+/g, " ").split(" ");
  processedWords = rawWords.map((rawWord, index) => {
    const match = rawWord.match(/^([a-zA-Z0-9'-]+)([^a-zA-Z0-9'-]*)$/);
    return {
      index: index,
      rawWord: rawWord,
      spellingTarget: match ? match[1] : rawWord,
      punctuation: match ? match[2] : ''
    };
  });

  if (isScrambleMode) {
    setupScrambleMode();
  } else {
    setupSpellingMode();
  }

  if (autoSpeak) {
    speakText(sentenceData.english);
  }

  saveSettingsToLocalStorage();
}

function updateStatusTags(status) {
  if (status === "mastered") {
    btnMarkMastered.classList.add("active");
    btnMarkMastered.innerHTML = '<i class="fa-solid fa-circle-check"></i> 已掌握';
    btnMarkReview.classList.remove("active");
    btnMarkReview.innerHTML = '<i class="fa-regular fa-circle-question"></i> 複習';
  } else if (status === "review") {
    btnMarkMastered.classList.remove("active");
    btnMarkMastered.innerHTML = '<i class="fa-regular fa-circle-check"></i> 掌握';
    btnMarkReview.classList.add("active");
    btnMarkReview.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> 待複習';
  } else {
    btnMarkMastered.classList.remove("active");
    btnMarkMastered.innerHTML = '<i class="fa-regular fa-circle-check"></i> 掌握';
    btnMarkReview.classList.remove("active");
    btnMarkReview.innerHTML = '<i class="fa-regular fa-circle-question"></i> 複習';
  }
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function noteRow(label, value) {
  if (!value) return "";
  return `<div class="ai-note-row"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></div>`;
}

function renderSentenceAiNote(note) {
  if (!sentenceAiResult || !sentenceAiContent || !note) return;
  sentenceAiContent.innerHTML = [
    noteRow("Translation", note.chinese || note.ai_chinese),
    noteRow("Grammar", note.grammar_note),
    noteRow("Vocabulary", note.vocabulary_note),
    noteRow("Common Mistakes", note.common_mistakes),
    noteRow("Example", note.example || note.ai_example),
  ].join("");
  sentenceAiResult.classList.remove("hidden");
}

function renderSavedSentenceAiNote(sentenceData) {
  if (!sentenceAiResult || !sentenceAiContent) return;

  if (sentenceData.grammar_note || sentenceData.vocabulary_note || sentenceData.ai_chinese) {
    renderSentenceAiNote(sentenceData);
  } else {
    sentenceAiResult.classList.add("hidden");
    sentenceAiContent.innerHTML = "";
  }

  if (sentenceExplainBtnText) {
    sentenceExplainBtnText.textContent = sentenceData.grammar_note ? "Show Saved Notes" : "AI Sentence Notes";
  }
}

function renderWordNote(note) {
  if (!wordNoteResult || !wordNoteContent || !note) return;
  wordNoteContent.innerHTML = [
    noteRow("Word", note.word),
    noteRow("IPA", note.ipa),
    noteRow("Syllables", note.syllables),
    noteRow("Stress", note.stress),
    noteRow("Meaning", note.meaning_zh),
    noteRow("Pronunciation", note.pronunciation_note),
    noteRow("Example", note.example),
  ].join("");
  wordNoteResult.classList.remove("hidden");
}

function clearWordNote() {
  if (wordNoteResult) wordNoteResult.classList.add("hidden");
  if (wordNoteContent) wordNoteContent.innerHTML = "";
  if (wordLookupInput) wordLookupInput.value = "";
}

async function triggerSentenceAiExplain() {
  if (currentMode !== "sentence" || currentSentences.length === 0) return;

  const sentenceData = currentSentences[currentSentenceIndex];
  if (sentenceData.grammar_note || sentenceData.vocabulary_note) {
    renderSentenceAiNote(sentenceData);
    return;
  }

  sentenceExplainBtnText.textContent = "AI analyzing...";
  btnSentenceExplain.disabled = true;

  try {
    const response = await fetch(`/api/sentences/${sentenceData.id}/ai-explain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.error || "AI sentence analysis failed");
    }

    const note = result.note;
    sentenceData.ai_chinese = note.chinese;
    sentenceData.grammar_note = note.grammar_note;
    sentenceData.vocabulary_note = note.vocabulary_note;
    sentenceData.common_mistakes = note.common_mistakes;
    sentenceData.ai_example = note.example;
    renderSentenceAiNote(sentenceData);
    sentenceExplainBtnText.textContent = "Show Saved Notes";
  } catch (e) {
    console.error("Sentence AI explain error:", e);
    alert(e.message || "AI sentence analysis failed");
    sentenceExplainBtnText.textContent = "AI Sentence Notes";
  } finally {
    btnSentenceExplain.disabled = false;
  }
}

async function triggerWordLookup() {
  if (currentMode !== "sentence" || currentSentences.length === 0) return;

  const word = (wordLookupInput.value || "").trim();
  if (!word) {
    wordLookupInput.focus();
    return;
  }

  const sentenceData = currentSentences[currentSentenceIndex];
  btnWordLookup.disabled = true;
  btnWordLookup.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> IPA';

  try {
    const response = await fetch("/api/words/lookup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        word,
        sentence: sentenceData.english
      })
    });
    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.error || "Word lookup failed");
    }

    renderWordNote(result.note);
  } catch (e) {
    console.error("Word lookup error:", e);
    alert(e.message || "Word lookup failed");
  } finally {
    btnWordLookup.disabled = false;
    btnWordLookup.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> IPA';
  }
}

/* ----------------- Spelling Mode Setup ----------------- */

function setupSpellingMode() {
  spellingZone.classList.remove("hidden");
  scrambleZone.classList.add("hidden");
  spellingZone.innerHTML = "";

  processedWords.forEach((wordData) => {
    const targetLength = wordData.spellingTarget.length;
    const block = document.createElement("div");
    block.className = "word-block";
    block.dataset.index = wordData.index;

    const input = document.createElement("input");
    input.type = "text";
    input.className = "word-input";
    input.maxLength = targetLength;
    input.style.width = `${Math.max(targetLength * 18 + 16, 30)}px`;
    input.autocomplete = "off";
    input.spellcheck = false;
    input.autocapitalize = "none";
    input.setAttribute("data-word-target", wordData.spellingTarget);

    const underline = document.createElement("div");
    underline.className = "word-underline";

    block.appendChild(input);
    block.appendChild(underline);
    spellingZone.appendChild(block);

    if (wordData.punctuation) {
      const punct = document.createElement("span");
      punct.className = "punctuation-mark";
      punct.textContent = wordData.punctuation;
      spellingZone.appendChild(punct);
    }

    input.addEventListener("input", (e) => handleWordInput(e, input, block, wordData));
    input.addEventListener("keydown", (e) => handleWordKeydown(e, input, block, wordData));
  });

  focusWordBlock(0);
}

function focusWordBlock(index) {
  const blocks = spellingZone.querySelectorAll(".word-block");
  blocks.forEach(b => b.classList.remove("active"));
  
  const targetBlock = spellingZone.querySelector(`.word-block[data-index="${index}"]`);
  if (targetBlock) {
    targetBlock.classList.add("active");
    const input = targetBlock.querySelector(".word-input");
    input.focus();
  }
}

function handleWordInput(e, input, block, wordData) {
  const target = wordData.spellingTarget.toLowerCase();
  const val = input.value.toLowerCase();

  if (target.startsWith(val)) {
    block.classList.remove("error");
    if (val === target) {
      block.classList.add("correct");
      const nextIndex = wordData.index + 1;
      const nextBlock = spellingZone.querySelector(`.word-block[data-index="${nextIndex}"]`);
      if (nextBlock) {
        focusWordBlock(nextIndex);
      } else {
        checkSpellingSentenceCorrect();
      }
    }
  } else {
    block.classList.add("error");
    block.classList.remove("correct");
  }
}

function handleWordKeydown(e, input, block, wordData) {
  const val = input.value;
  const target = wordData.spellingTarget;

  if (e.key === " " || e.code === "Space") {
    e.preventDefault();
    if (val.toLowerCase() === target.toLowerCase()) {
      block.classList.add("correct");
      const nextIndex = wordData.index + 1;
      focusWordBlock(nextIndex);
    } else if (val.length > 0) {
      const nextIndex = wordData.index + 1;
      focusWordBlock(nextIndex);
    }
  }
  else if (e.key === "Backspace" && val === "") {
    e.preventDefault();
    const prevIndex = wordData.index - 1;
    const prevBlock = spellingZone.querySelector(`.word-block[data-index="${prevIndex}"]`);
    if (prevBlock) {
      focusWordBlock(prevIndex);
      const prevInput = prevBlock.querySelector(".word-input");
      prevInput.value = prevInput.value.slice(0, -1);
      prevInput.dispatchEvent(new Event("input"));
    }
  }
  else if (e.key === "ArrowLeft") {
    const prevIndex = wordData.index - 1;
    if (prevIndex >= 0) {
      e.preventDefault();
      focusWordBlock(prevIndex);
    }
  }
  else if (e.key === "ArrowRight") {
    const nextIndex = wordData.index + 1;
    if (nextIndex < processedWords.length) {
      e.preventDefault();
      focusWordBlock(nextIndex);
    }
  }
}

function resetCurrentInputs() {
  if (currentMode === "toeic") {
    resetToeicOptions();
  } else if (currentMode === "toeic-part2") {
    resetPart2Options();
  } else {
    if (isScrambleMode) {
      setupScrambleMode();
    } else {
      const inputs = spellingZone.querySelectorAll(".word-input");
      const blocks = spellingZone.querySelectorAll(".word-block");
      inputs.forEach(i => i.value = "");
      blocks.forEach(b => {
        b.classList.remove("correct");
        b.classList.remove("error");
        b.classList.remove("active");
      });
      focusWordBlock(0);
    }
  }
}

function checkSpellingSentenceCorrect() {
  const blocks = spellingZone.querySelectorAll(".word-block");
  let allCorrect = true;

  blocks.forEach(block => {
    const input = block.querySelector(".word-input");
    const target = input.getAttribute("data-word-target");
    if (input.value.toLowerCase() !== target.toLowerCase()) {
      allCorrect = false;
      block.classList.add("error");
    }
  });

  if (allCorrect) {
    if (!sentenceRewardGiven) {
      rewardPet("sentence");
      sentenceRewardGiven = true;
    }
    if (correctSpeak) {
      speakText(currentSentences[currentSentenceIndex].english);
    }
    spellingZone.classList.add("all-correct-pulse");
    setTimeout(() => spellingZone.classList.remove("all-correct-pulse"), 1000);
  } else {
    resetPetStreak();
  }
  return allCorrect;
}

/* ----------------- Scramble Mode Setup ----------------- */

function setupScrambleMode() {
  spellingZone.classList.add("hidden");
  scrambleZone.classList.remove("hidden");
  scrambleSlots.innerHTML = "";
  scrambleOptions.innerHTML = "";
  scrambleSelections = [];

  processedWords.forEach((wordData, i) => {
    const slot = document.createElement("div");
    slot.className = "scramble-slot-empty";
    slot.style.minWidth = "80px";
    slot.style.height = "40px";
    slot.style.borderBottom = "2px dashed rgba(255, 255, 255, 0.15)";
    slot.dataset.index = i;
    scrambleSlots.appendChild(slot);
  });

  const shuffledOptions = processedWords
    .map(w => ({ originalIndex: w.index, word: w.rawWord }))
    .sort(() => Math.random() - 0.5);

  shuffledOptions.forEach((opt, arrayIndex) => {
    const card = document.createElement("div");
    card.className = "word-card";
    card.dataset.originalIndex = opt.originalIndex;
    card.dataset.optionIndex = arrayIndex;
    
    if (arrayIndex < 9) {
      const indexBadge = document.createElement("span");
      indexBadge.className = "word-card-index";
      indexBadge.textContent = arrayIndex + 1;
      card.appendChild(indexBadge);
    }
    
    const wordText = document.createElement("span");
    wordText.textContent = opt.word;
    card.appendChild(wordText);

    scrambleOptions.appendChild(card);
    card.addEventListener("click", () => selectScrambleCard(card));
  });
}

function selectScrambleCard(card) {
  if (card.classList.contains("selected")) return;

  const originalIndex = parseInt(card.dataset.originalIndex, 10);
  const word = card.textContent.replace(/[1-9]/g, "").trim();

  card.classList.add("selected");
  scrambleSelections.push({
    cardElement: card,
    originalIndex: originalIndex,
    word: word
  });

  renderScrambleSlots();
  checkScrambleFinished();
}

function deselectScrambleSlot(slotIndex) {
  if (slotIndex >= scrambleSelections.length) return;
  
  const selection = scrambleSelections[slotIndex];
  selection.cardElement.classList.remove("selected");
  scrambleSelections.splice(slotIndex, 1);

  renderScrambleSlots();
}

function renderScrambleSlots() {
  const slots = scrambleSlots.children;
  for (let i = 0; i < slots.length; i++) {
    slots[i].innerHTML = "";
    slots[i].className = "scramble-slot-empty";
  }

  scrambleSelections.forEach((sel, i) => {
    const slot = slots[i];
    slot.className = "scramble-slot-filled";
    
    const badge = document.createElement("div");
    badge.className = "word-card";
    badge.textContent = sel.word;
    badge.addEventListener("click", () => deselectScrambleSlot(i));
    
    slot.appendChild(badge);
  });
}

function checkScrambleFinished() {
  if (scrambleSelections.length === processedWords.length) {
    let isCorrect = true;
    for (let i = 0; i < scrambleSelections.length; i++) {
      if (scrambleSelections[i].originalIndex !== i) {
        isCorrect = false;
        break;
      }
    }

    if (isCorrect) {
      if (!sentenceRewardGiven) {
        rewardPet("sentence");
        sentenceRewardGiven = true;
      }
      const activeText = currentSentences[currentSentenceIndex].english;
      if (correctSpeak) {
        speakText(activeText);
      }
      scrambleSlots.classList.add("all-correct-pulse");
      setTimeout(() => scrambleSlots.classList.remove("all-correct-pulse"), 1000);
    } else {
      resetPetStreak();
      scrambleSlots.classList.add("error-pulse");
      setTimeout(() => scrambleSlots.classList.remove("error-pulse"), 800);
    }
  }
}

/* ----------------- API Integration: TOEIC Practice Mode ----------------- */

// Fetch TOEIC questions list from SQLite
async function fetchToeicQuestions() {
  // Determine chunk offset
  const offset = Math.floor(currentToeicIndex / 50) * 50;

  try {
    const response = await fetch(`/api/toeic/questions?limit=50&offset=${offset}&status=${currentFilter}&category=${currentCategory}`);
    const result = await response.json();
    toeicQuestions = result.questions;
    totalToeicCount = result.total;

    if (toeicQuestions.length === 0) {
      if (currentFilter !== "all" || currentCategory !== "all") {
        alert("此篩選條件下沒有任何題目！將為您重置篩選條件。");
        toeicFilter.value = "all";
        currentFilter = "all";
        toeicCategoryFilter.value = "all";
        currentCategory = "all";
        fetchToeicQuestions();
      } else {
        alert("資料庫中沒有任何多益題目！請執行 import_toeic.py。");
      }
      return;
    }

    loadToeicQuestion();
  } catch (e) {
    console.error("Failed to load TOEIC questions:", e);
    alert("連接多益題庫失敗！");
  }
}

// Load current active TOEIC question
function loadToeicQuestion() {
  if (toeicQuestions.length === 0) return;

  // Question index modulo 50 matches the loaded chunk array offset
  const indexInChunk = currentToeicIndex % 50;
  const question = toeicQuestions[indexInChunk];
  
  if (!question) {
    // If indices went out of sync
    currentToeicIndex = 0;
    loadToeicQuestion();
    return;
  }

  isToeicAnswered = false;

  // Update progress bar
  progressIndicator.textContent = `多益 Part 5 | ${currentToeicIndex + 1} / ${totalToeicCount}`;
  const percentage = ((currentToeicIndex + 1) / totalToeicCount) * 100;
  progressBarFill.style.width = `${percentage}%`;

  // Status markings
  updateStatusTags(question.status);

  // Parse and display the question text. Replace "___", "____" with the blank span
  const rawQ = question.question;
  const formattedQ = rawQ.replace(/___+/g, '<span class="toeic-blank">________</span>')
                          .replace(/_+/g, '<span class="toeic-blank">________</span>');
  toeicQuestionText.innerHTML = formattedQ;

  // Set option buttons text
  const opts = [
    { key: "A", text: question.option_a },
    { key: "B", text: question.option_b },
    { key: "C", text: question.option_c },
    { key: "D", text: question.option_d }
  ];

  toeicOptButtons.forEach((btn, idx) => {
    const opt = opts[idx];
    btn.dataset.option = opt.key;
    btn.querySelector(".opt-text").textContent = opt.text;
    
    // Reset buttons styles
    btn.className = "toeic-opt-btn";
  });

  // Reset answer hints
  answerHint.classList.add("hidden");
  explanationBox.classList.add("hidden");
  chinesePrompt.classList.add("hidden"); // Hide Chinese translation by default

  // Always show explain/hint button before answering
  btnToeicExplain.classList.remove("hidden");
  btnToeicExplain.disabled = false;

  // Check if Chinese translation already exists in DB
  if (question.chinese) {
    explainBtnText.textContent = "顯示中文提示";
    setupToeicExplanationUI(question);
  } else {
    explainBtnText.textContent = "AI 翻譯與解析";
  }

  // Auto-speak the completed correct sentence
  if (autoSpeak) {
    speakToeicSentence(question);
  }

  saveSettingsToLocalStorage();
}

function getOptionText(question, optionKey) {
  if (optionKey === "A") return question.option_a;
  if (optionKey === "B") return question.option_b;
  if (optionKey === "C") return question.option_c;
  if (optionKey === "D") return question.option_d;
  return "";
}

function speakToeicSentence(question) {
  // Replace the blank with the correct answer option text to speak a natural complete sentence
  const completedText = question.question.replace(/___+/g, getOptionText(question, question.answer))
                                         .replace(/_+/g, getOptionText(question, question.answer));
  speakText(completedText);
}

// Select an option (作答)
function selectToeicOption(selectedOption) {
  if (isToeicAnswered || toeicQuestions.length === 0) return;
  
  isToeicAnswered = true;
  const indexInChunk = currentToeicIndex % 50;
  const question = toeicQuestions[indexInChunk];
  const correctAnswer = question.answer; // 'A', 'B', 'C', or 'D'

  // Disable all buttons and show colors
  toeicOptButtons.forEach(btn => {
    btn.classList.add("disabled");
    const btnOpt = btn.dataset.option;
    
    if (btnOpt === correctAnswer) {
      btn.classList.add("correct");
    } else if (btnOpt === selectedOption) {
      btn.classList.add("error");
    }
  });

  // TTS if correct speak enabled
  if (selectedOption === correctAnswer) {
    rewardPet("toeic");
    if (correctSpeak) {
      speakToeicSentence(question);
    }
  } else {
    resetPetStreak();
  }

  // Setup answer overlays
  revealToeicAnswer(question);
}

function revealToeicAnswer(question) {
  // Show answer text
  const ansText = getOptionText(question, question.answer);
  englishAnswer.textContent = `(${question.answer}) ${ansText}`;
  answerHint.classList.remove("hidden");

  if (question.chinese) {
    chinesePrompt.textContent = question.chinese;
    chinesePrompt.classList.remove("hidden");
    explanationBox.classList.remove("hidden");
    btnToeicExplain.classList.add("hidden"); // Hide hint button since explanation is shown
  } else {
    chinesePrompt.classList.add("hidden");
    explanationBox.classList.add("hidden");
    btnToeicExplain.classList.remove("hidden");
    explainBtnText.textContent = "AI 翻譯與解析";
  }
}

function setupToeicExplanationUI(question) {
  chinesePrompt.textContent = question.chinese;
  toeicExplanation.textContent = question.explanation;
}

// Trigger AI generating explanation via API / Toggle Hint
async function triggerAiExplanation() {
  if (toeicQuestions.length === 0) return;

  const indexInChunk = currentToeicIndex % 50;
  const question = toeicQuestions[indexInChunk];

  // If translation already exists, just toggle hint visibility
  if (question.chinese) {
    if (chinesePrompt.classList.contains("hidden")) {
      chinesePrompt.classList.remove("hidden");
      explainBtnText.textContent = "隱藏中文提示";
    } else {
      chinesePrompt.classList.add("hidden");
      explainBtnText.textContent = "顯示中文提示";
    }
    return;
  }

  explainBtnText.textContent = "AI 分析中...";
  btnToeicExplain.disabled = true;

  try {
    const response = await fetch(`/api/toeic/questions/${question.id}/ai-explain`, {
      method: "POST"
    });
    const result = await response.json();

    if (result.success) {
      // Save details locally in state
      question.chinese = result.chinese;
      question.explanation = result.explanation;
      
      // Update UI elements
      setupToeicExplanationUI(question);
      
      // Since it's now loaded, show it as a hint or show everything if answered
      if (isToeicAnswered) {
        revealToeicAnswer(question);
      } else {
        chinesePrompt.classList.remove("hidden");
        explainBtnText.textContent = "隱藏中文提示";
        btnToeicExplain.disabled = false;
      }
    } else {
      alert("AI 生成失敗：" + result.error);
      explainBtnText.textContent = "AI 翻譯與解析";
      btnToeicExplain.disabled = false;
      
      // If error is due to missing key, automatically pop up settings
      if (result.error && result.error.includes("金鑰")) {
        voiceModal.classList.add("show");
        geminiKeyInput.focus();
      }
    }
  } catch (e) {
    console.error("AI Explain request error:", e);
    alert("無法連接到 AI 解析服務。");
    explainBtnText.textContent = "AI 翻譯與解析";
    btnToeicExplain.disabled = false;
  }
}

function resetToeicOptions() {
  // Re-enable options
  isToeicAnswered = false;
  toeicOptButtons.forEach(btn => {
    btn.className = "toeic-opt-btn";
  });
  answerHint.classList.add("hidden");
  explanationBox.classList.add("hidden");
  chinesePrompt.classList.add("hidden");
}

/* ----------------- API Integration: TOEIC Part 2 Practice Mode ----------------- */

// Fetch TOEIC Part 2 questions list from SQLite
async function fetchToeicPart2Questions() {
  const offset = Math.floor(currentPart2Index / 50) * 50;

  try {
    const response = await fetch(`/api/toeic/part2/questions?limit=50&offset=${offset}&status=${currentFilter}`);
    const result = await response.json();
    toeicPart2Questions = result.questions;
    totalPart2Count = result.total;

    if (toeicPart2Questions.length === 0) {
      if (currentFilter !== "all") {
        alert("此篩選條件下沒有任何題目！將為您切換回「全部題目」。");
        toeicFilter.value = "all";
        currentFilter = "all";
        fetchToeicPart2Questions();
      } else {
        alert("資料庫中沒有任何多益聽力應答題目！請執行 import_part2.py。");
      }
      return;
    }

    loadToeicPart2Question();
  } catch (e) {
    console.error("Failed to load TOEIC Part 2 questions:", e);
    alert("連接多益聽力題庫失敗！");
  }
}

// Load current active TOEIC Part 2 question
function loadToeicPart2Question() {
  if (toeicPart2Questions.length === 0) return;

  const indexInChunk = currentPart2Index % 50;
  const question = toeicPart2Questions[indexInChunk];
  
  if (!question) {
    currentPart2Index = 0;
    loadToeicPart2Question();
    return;
  }

  isPart2Answered = false;

  // Update progress bar
  progressIndicator.textContent = `多益 Part 2 | ${currentPart2Index + 1} / ${totalPart2Count}`;
  const percentage = ((currentPart2Index + 1) / totalPart2Count) * 100;
  progressBarFill.style.width = `${percentage}%`;

  // Status markings
  updateStatusTags(question.status);

  // Set transcript text ready (hidden initially)
  toeicPart2QuestionText.textContent = question.question;
  part2TranscriptA.textContent = question.option_a;
  part2TranscriptB.textContent = question.option_b;
  part2TranscriptC.textContent = question.option_c;

  // Re-enable and reset option buttons
  toeicPart2OptButtons.forEach((btn) => {
    btn.className = "toeic-part2-opt-btn toeic-opt-btn";
  });

  // Reset transcript reveal view
  part2QuestionReveal.classList.add("hidden");

  // Reset AI explanation button & box
  if (question.chinese) {
    btnPart2Explain.classList.add("hidden");
    setupPart2ExplanationUI(question);
  } else {
    btnPart2Explain.classList.remove("hidden");
    part2ExplainBtnText.textContent = "AI 翻譯與解析";
    btnPart2Explain.disabled = false;
    part2ExplanationBox.classList.add("hidden");
  }

  // Load audio source and reset audio player state
  audioPart2Player.pause();
  audioPart2Player.currentTime = 0;
  audioPart2Player.src = `/api/toeic/part2/questions/${question.id}/audio`;
  
  btnPart2Play.innerHTML = '<i class="fa-solid fa-play"></i>';
  toeicPart2StatusText.textContent = "點擊播放鈕或按 Space 聆聽題目與選項";

  // Auto-play the audio
  if (autoSpeak) {
    playPart2Audio();
  }

  saveSettingsToLocalStorage();
}

function playPart2Audio() {
  audioPart2Player.play().then(() => {
    btnPart2Play.innerHTML = '<i class="fa-solid fa-pause"></i>';
    toeicPart2StatusText.textContent = "播放中...";
  }).catch(err => {
    console.error("Audio playback failed:", err);
    toeicPart2StatusText.textContent = "音訊生成中，請稍候...";
  });
}

function pausePart2Audio() {
  audioPart2Player.pause();
  btnPart2Play.innerHTML = '<i class="fa-solid fa-play"></i>';
  toeicPart2StatusText.textContent = "已暫停，按 Space 繼續播放";
}

function togglePart2Audio() {
  if (audioPart2Player.paused) {
    playPart2Audio();
  } else {
    pausePart2Audio();
  }
}

function selectPart2Option(selectedOption) {
  if (isPart2Answered || toeicPart2Questions.length === 0) return;
  
  isPart2Answered = true;
  const indexInChunk = currentPart2Index % 50;
  const question = toeicPart2Questions[indexInChunk];
  const correctAnswer = question.answer; // 'A', 'B', or 'C'

  // Disable all buttons and show colors
  toeicPart2OptButtons.forEach(btn => {
    btn.classList.add("disabled");
    const btnOpt = btn.dataset.option;
    
    if (btnOpt === correctAnswer) {
      btn.classList.add("correct");
    } else if (btnOpt === selectedOption) {
      btn.classList.add("error");
    }
  });

  // Reveal transcription and detailed option text
  part2QuestionReveal.classList.remove("hidden");

  if (selectedOption === correctAnswer) {
    rewardPet("part2");
  } else {
    resetPetStreak();
  }
  
  // Pause audio if playing
  pausePart2Audio();
}

function setupPart2ExplanationUI(question) {
  part2ExplanationBox.classList.remove("hidden");
  toeicPart2Explanation.innerHTML = `<strong>翻譯：</strong><br>${question.chinese.replace(/\n/g, "<br>")}<br><br><strong>解析：</strong><br>${question.explanation.replace(/\n/g, "<br>")}`;
}

async function triggerPart2AiExplanation() {
  if (toeicPart2Questions.length === 0) return;

  const indexInChunk = currentPart2Index % 50;
  const question = toeicPart2Questions[indexInChunk];

  part2ExplainBtnText.textContent = "AI 分析中...";
  btnPart2Explain.disabled = true;

  try {
    const response = await fetch(`/api/toeic/part2/questions/${question.id}/ai-explain`, {
      method: "POST"
    });
    const result = await response.json();

    if (result.success) {
      // Save details locally in state
      question.chinese = result.chinese;
      question.explanation = result.explanation;
      
      // Update UI
      setupPart2ExplanationUI(question);
      btnPart2Explain.classList.add("hidden");
    } else {
      alert("AI 生成失敗：" + result.error);
      part2ExplainBtnText.textContent = "AI 翻譯與解析";
      btnPart2Explain.disabled = false;
      
      if (result.error && result.error.includes("金鑰")) {
        voiceModal.classList.add("show");
        geminiKeyInput.focus();
      }
    }
  } catch (e) {
    console.error("AI Explain request error:", e);
    alert("無法連接到 AI 解析服務。");
    part2ExplainBtnText.textContent = "AI 翻譯與解析";
    btnPart2Explain.disabled = false;
  }
}

function resetPart2Options() {
  isPart2Answered = false;
  toeicPart2OptButtons.forEach(btn => {
    btn.className = "toeic-part2-opt-btn toeic-opt-btn";
  });
  part2QuestionReveal.classList.add("hidden");
  part2ExplanationBox.classList.add("hidden");
}

/* ----------------- Navigation & Mark Status APIs ----------------- */

function nextQuestion() {
  if (currentMode === "toeic") {
    if (currentToeicIndex < totalToeicCount - 1) {
      currentToeicIndex++;
      
      // If we crossed a 50 boundary, fetch the next page chunk
      if (currentToeicIndex % 50 === 0) {
        fetchToeicQuestions();
      } else {
        loadToeicQuestion();
      }
    } else {
      alert("恭喜！您已完成全部多益模擬題！");
    }
  } else if (currentMode === "toeic-part2") {
    if (currentPart2Index < totalPart2Count - 1) {
      currentPart2Index++;
      
      if (currentPart2Index % 50 === 0) {
        fetchToeicPart2Questions();
      } else {
        loadToeicPart2Question();
      }
    } else {
      alert("恭喜！您已完成全部聽力應答題！");
    }
  } else {
    if (currentSentenceIndex < currentSentences.length - 1) {
      currentSentenceIndex++;
      loadSentence();
    } else {
      alert("恭喜！您已完成本單元的所有句子！");
    }
  }
}

function prevQuestion() {
  if (currentMode === "toeic") {
    if (currentToeicIndex > 0) {
      currentToeicIndex--;
      
      // If we crossed a 50 boundary backwards, fetch the previous page chunk
      if ((currentToeicIndex + 1) % 50 === 0) {
        fetchToeicQuestions();
      } else {
        loadToeicQuestion();
      }
    }
  } else if (currentMode === "toeic-part2") {
    if (currentPart2Index > 0) {
      currentPart2Index--;
      
      if ((currentPart2Index + 1) % 50 === 0) {
        fetchToeicPart2Questions();
      } else {
        loadToeicPart2Question();
      }
    }
  } else {
    if (currentSentenceIndex > 0) {
      currentSentenceIndex--;
      loadSentence();
    }
  }
}

function toggleAnswer() {
  isAnswerShowing = !isAnswerShowing;
  if (isAnswerShowing) {
    if (currentMode === "toeic") {
      answerHint.classList.remove("hidden");
      const indexInChunk = currentToeicIndex % 50;
      const question = toeicQuestions[indexInChunk];
      revealToeicAnswer(question);
    } else if (currentMode === "toeic-part2") {
      part2QuestionReveal.classList.remove("hidden");
    } else {
      answerHint.classList.remove("hidden");
    }
  } else {
    answerHint.classList.add("hidden");
    explanationBox.classList.add("hidden");
    if (currentMode === "toeic") {
      chinesePrompt.classList.add("hidden");
    } else if (currentMode === "toeic-part2") {
      part2QuestionReveal.classList.add("hidden");
    }
  }
}

// Mark status as mastered (SQLite Integration)
async function markMastered() {
  if (currentMode === "toeic") {
    if (toeicQuestions.length === 0) return;
    const question = toeicQuestions[currentToeicIndex % 50];
    const newStatus = question.status === "mastered" ? "new" : "mastered";

    try {
      const response = await fetch(`/api/toeic/questions/${question.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const result = await response.json();
      if (result.success) {
        question.status = newStatus;
        loadToeicQuestion();
      }
    } catch (e) {
      console.error("Failed to update status:", e);
    }
  } else if (currentMode === "toeic-part2") {
    if (toeicPart2Questions.length === 0) return;
    const question = toeicPart2Questions[currentPart2Index % 50];
    const newStatus = question.status === "mastered" ? "new" : "mastered";

    try {
      const response = await fetch(`/api/toeic/part2/questions/${question.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const result = await response.json();
      if (result.success) {
        question.status = newStatus;
        loadToeicPart2Question();
      }
    } catch (e) {
      console.error("Failed to update status:", e);
    }
  } else {
    if (currentSentences.length === 0) return;
    const sentence = currentSentences[currentSentenceIndex];
    const newStatus = sentence.status === "mastered" ? "new" : "mastered";

    try {
      const response = await fetch(`/api/sentences/${sentence.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const result = await response.json();
      if (result.success) {
        sentence.status = newStatus;
        loadSentence();
      }
    } catch (e) {
      console.error("Failed to update status:", e);
    }
  }
}

// Mark status as review (SQLite Integration)
async function markReview() {
  if (currentMode === "toeic") {
    if (toeicQuestions.length === 0) return;
    const question = toeicQuestions[currentToeicIndex % 50];
    const newStatus = question.status === "review" ? "new" : "review";

    try {
      const response = await fetch(`/api/toeic/questions/${question.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const result = await response.json();
      if (result.success) {
        question.status = newStatus;
        loadToeicQuestion();
      }
    } catch (e) {
      console.error("Failed to update status:", e);
    }
  } else if (currentMode === "toeic-part2") {
    if (toeicPart2Questions.length === 0) return;
    const question = toeicPart2Questions[currentPart2Index % 50];
    const newStatus = question.status === "review" ? "new" : "review";

    try {
      const response = await fetch(`/api/toeic/part2/questions/${question.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const result = await response.json();
      if (result.success) {
        question.status = newStatus;
        loadToeicPart2Question();
      }
    } catch (e) {
      console.error("Failed to update status:", e);
    }
  } else {
    if (currentSentences.length === 0) return;
    const sentence = currentSentences[currentSentenceIndex];
    const newStatus = sentence.status === "review" ? "new" : "review";

    try {
      const response = await fetch(`/api/sentences/${sentence.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const result = await response.json();
      if (result.success) {
        sentence.status = newStatus;
        loadSentence();
      }
    } catch (e) {
      console.error("Failed to update status:", e);
    }
  }
}

/* ----------------- Speech Synthesizer (TTS) ----------------- */

function speakText(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices();
  const selectedVoice = voices.find(v => v.name === selectedVoiceName);
  if (selectedVoice) {
    utterance.voice = selectedVoice;
  }

  utterance.rate = speechRate;
  window.speechSynthesis.speak(utterance);
}

/* ----------------- Bulk Import AI Sentences ----------------- */

async function handleImportText() {
  const text = importTextarea.value.trim();
  const unitName = importUnitName.value.trim() || "自訂 AI 單元";

  if (!text) {
    alert("請輸入有效的句子內容！");
    return;
  }

  const lines = text.split("\n");
  const parsedSentences = [];

  lines.forEach(line => {
    let english = "";
    let chinese = "";

    const separators = [" / ", " | ", " - ", "/"];
    for (let sep of separators) {
      if (line.includes(sep)) {
        const parts = line.split(sep);
        if (parts.length >= 2) {
          english = parts[0].trim();
          chinese = parts[1].trim();
          break;
        }
      }
    }

    if (!english && !chinese) {
      const matches = line.match(/^([a-zA-Z0-9\s.,?!'"-]+)[\s\t]+([\u4e00-\u9fa5\s.,?!，。？！]+)$/);
      if (matches) {
        english = matches[1].trim();
        chinese = matches[2].trim();
      }
    }

    if (english && chinese) {
      parsedSentences.push({ english, chinese });
    }
  });

  if (parsedSentences.length === 0) {
    try {
      const jsonParsed = JSON.parse(text);
      if (Array.isArray(jsonParsed)) {
        jsonParsed.forEach(item => {
          if ((item.english || item.eng) && (item.chinese || item.chi || item.zho)) {
            parsedSentences.push({
              english: item.english || item.eng,
              chinese: item.chinese || item.chi || item.zho
            });
          }
        });
      }
    } catch(e) {}
  }

  if (parsedSentences.length === 0) {
    alert("無法解析句子，請檢查格式是否符合「英文 / 中文」。");
    return;
  }

  try {
    const response = await fetch("/api/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        unit_name: unitName,
        sentences: parsedSentences
      })
    });
    
    const result = await response.json();
    if (result.success) {
      importModal.classList.remove("show");
      importTextarea.value = "";
      alert(`成功導入 ${result.inserted_count} 個句子！`);
      fetchUnits(result.unit_id);
    } else {
      alert("導入失敗：" + result.error);
    }
  } catch (e) {
    console.error("Import request failed:", e);
    alert("無法連接到伺服器進行導入。");
  }
}

/* ----------------- Event Registrations & Global Shortcuts ----------------- */

function registerEventListeners() {
  // Tab buttons
  tabSentence.addEventListener("click", () => switchTab("sentence"));
  tabToeic.addEventListener("click", () => switchTab("toeic"));
  tabToeicPart2.addEventListener("click", () => switchTab("toeic-part2"));

  if (petCarePanel) {
    petCarePanel.addEventListener("click", (e) => {
      const skinButton = e.target.closest("[data-skin-id]");
      if (skinButton) {
        selectPetSkin(skinButton.dataset.skinId);
        return;
      }

      const itemButton = e.target.closest("[data-item-id]");
      if (itemButton) {
        usePetItem(itemButton.dataset.itemId);
        return;
      }

      const claimButton = e.target.closest("[data-quest-id]");
      if (claimButton) {
        claimPetDailyQuest(claimButton.dataset.questId);
      }
    });
  }

  // Dropdown Unit Selection change
  unitSelector.addEventListener("change", (e) => {
    activeUnitId = parseInt(e.target.value, 10);
    currentSentenceIndex = 0;
    saveSettingsToLocalStorage();
    fetchSentences(activeUnitId);
  });

  // Navigation button (prev unit)
  btnBack.addEventListener("click", () => {
    const currentIndex = units.findIndex(u => u.id === activeUnitId);
    if (currentIndex > 0) {
      activeUnitId = units[currentIndex - 1].id;
      unitSelector.value = activeUnitId;
      currentSentenceIndex = 0;
      saveSettingsToLocalStorage();
      fetchSentences(activeUnitId);
    }
  });

  btnReset.addEventListener("click", resetCurrentInputs);
  
  btnSpeak.addEventListener("click", () => {
    if (currentMode === "toeic") {
      if (toeicQuestions.length > 0) {
        speakToeicSentence(toeicQuestions[currentToeicIndex % 50]);
      }
    } else if (currentMode === "toeic-part2") {
      togglePart2Audio();
    } else {
      if (currentSentences.length > 0) {
        speakText(currentSentences[currentSentenceIndex].english);
      }
    }
  });

  // Part 2 Audio Buttons & Player Event Listeners
  btnPart2Play.addEventListener("click", () => {
    togglePart2Audio();
  });

  audioPart2Player.addEventListener("ended", () => {
    btnPart2Play.innerHTML = '<i class="fa-solid fa-play"></i>';
    toeicPart2StatusText.textContent = "播放完畢，請作答";
  });

  audioPart2Player.addEventListener("error", (e) => {
    console.error("Audio error:", e);
    btnPart2Play.innerHTML = '<i class="fa-solid fa-play"></i>';
    toeicPart2StatusText.textContent = "音訊載入失敗，點擊重試";
  });

  modeScrambleToggle.addEventListener("change", (e) => {
    isScrambleMode = e.target.checked;
    loadSentence();
  });

  btnImport.addEventListener("click", () => {
    importModal.classList.add("show");
    importTextarea.focus();
  });

  btnTtsSettings.addEventListener("click", () => {
    voiceModal.classList.add("show");
    fetchConfigSettings(); // Load API key configuration
  });

  modalClose.addEventListener("click", () => importModal.classList.remove("show"));
  btnImportCancel.addEventListener("click", () => importModal.classList.remove("show"));
  voiceModalClose.addEventListener("click", () => voiceModal.classList.remove("show"));
  
  btnVoiceClose.addEventListener("click", () => {
    saveConfigSettings(); // Save Gemini API Key if changed
    voiceModal.classList.remove("show");
  });

  window.addEventListener("click", (e) => {
    if (e.target === importModal) importModal.classList.remove("show");
    if (e.target === voiceModal) voiceModal.classList.remove("show");
  });

  btnImportSubmit.addEventListener("click", handleImportText);
  btnSentenceExplain.addEventListener("click", triggerSentenceAiExplain);
  btnWordLookup.addEventListener("click", triggerWordLookup);
  wordLookupInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      triggerWordLookup();
    }
  });
  btnToeicExplain.addEventListener("click", triggerAiExplanation);
  btnPart2Explain.addEventListener("click", triggerPart2AiExplanation);
  btnMarkMastered.addEventListener("click", markMastered);
  btnMarkReview.addEventListener("click", markReview);

  // Bind TOEIC option buttons
  toeicOptButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      selectToeicOption(btn.dataset.option);
    });
  });

  // Bind TOEIC Part 2 option buttons
  toeicPart2OptButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      selectPart2Option(btn.dataset.option);
    });
  });

  toeicFilter.addEventListener("change", (e) => {
    currentFilter = e.target.value;
    if (currentMode === "toeic") {
      currentToeicIndex = 0;
      fetchToeicQuestions();
    } else if (currentMode === "toeic-part2") {
      currentPart2Index = 0;
      fetchToeicPart2Questions();
    }
  });

  toeicCategoryFilter.addEventListener("change", (e) => {
    currentCategory = e.target.value;
    if (currentMode === "toeic") {
      currentToeicIndex = 0;
      fetchToeicQuestions();
    }
  });

  voiceSelect.addEventListener("change", (e) => {
    selectedVoiceName = e.target.value;
    saveSettingsToLocalStorage();
  });

  voiceSpeed.addEventListener("input", (e) => {
    speechRate = parseFloat(e.target.value);
    speedVal.textContent = speechRate.toFixed(1);
    saveSettingsToLocalStorage();
  });

  autoSpeakToggle.addEventListener("change", (e) => {
    autoSpeak = e.target.checked;
    saveSettingsToLocalStorage();
  });

  correctSpeakToggle.addEventListener("change", (e) => {
    correctSpeak = e.target.checked;
    saveSettingsToLocalStorage();
  });

  // Global Keyboard Shortcuts
  window.addEventListener("keydown", (e) => {
    // Disable shortcuts when typing inside form textboxes
    if (document.activeElement.tagName === "TEXTAREA" || 
        (document.activeElement.tagName === "INPUT" && 
         (document.activeElement.id === "import-unit-name" ||
          document.activeElement.id === "gemini-key-input" ||
          document.activeElement.id === "word-lookup-input"))) {
      return;
    }

    // Ctrl + N : Mark Mastered
    if (e.ctrlKey && e.key.toLowerCase() === "n") {
      e.preventDefault();
      markMastered();
    }
    // Ctrl + Q : Mark Review
    else if (e.ctrlKey && e.key.toLowerCase() === "q") {
      e.preventDefault();
      markReview();
    }
    // Shift + RightArrow: Next Question
    else if (e.shiftKey && e.key === "ArrowRight") {
      e.preventDefault();
      nextQuestion();
    }
    // Shift + LeftArrow: Previous Question
    else if (e.shiftKey && e.key === "ArrowLeft") {
      e.preventDefault();
      prevQuestion();
    }
    // ArrowUp or ArrowDown: Toggle Show Answer
    else if (e.key === "ArrowUp" || e.key === "ArrowDown") {
      e.preventDefault();
      toggleAnswer();
    }
    // Escape or Ctrl + R: Reset current inputs
    else if (e.key === "Escape" || (e.ctrlKey && e.key.toLowerCase() === "r")) {
      e.preventDefault();
      resetCurrentInputs();
    }
    // Ctrl or Alt keys alone: Speak Sentence / Play Audio
    else if (e.key === "Control" || e.key === "Alt") {
      if (currentMode === "toeic") {
        if (toeicQuestions.length > 0) {
          speakToeicSentence(toeicQuestions[currentToeicIndex % 50]);
        }
      } else if (currentMode === "toeic-part2") {
        togglePart2Audio();
      } else {
        if (currentSentences.length > 0) {
          speakText(currentSentences[currentSentenceIndex].english);
        }
      }
    }
    // Key E: Trigger AI Explain (TOEIC mode or Part 2 mode)
    else if (e.key.toLowerCase() === "e" && !e.ctrlKey && !e.shiftKey) {
      if (currentMode === "toeic") {
        const indexInChunk = currentToeicIndex % 50;
        const question = toeicQuestions[indexInChunk];
        if (question && !btnToeicExplain.disabled) {
          e.preventDefault();
          triggerAiExplanation();
        }
      } else if (currentMode === "toeic-part2") {
        const indexInChunk = currentPart2Index % 50;
        const question = toeicPart2Questions[indexInChunk];
        if (question && !question.chinese && !btnPart2Explain.disabled) {
          e.preventDefault();
          triggerPart2AiExplanation();
        }
      }
    }
    // Enter key: Validate / Advance
    else if (e.key === "Enter") {
      e.preventDefault();
      
      if (currentMode === "toeic") {
        // If answered, pressing Enter advances to next question
        if (isToeicAnswered) {
          nextQuestion();
        }
      } else if (currentMode === "toeic-part2") {
        // If answered, pressing Enter advances to next question
        if (isPart2Answered) {
          nextQuestion();
        }
      } else {
        if (isScrambleMode) {
          const isFinished = scrambleSelections.length === processedWords.length;
          if (isFinished) {
            let isCorrect = true;
            for (let i = 0; i < scrambleSelections.length; i++) {
              if (scrambleSelections[i].originalIndex !== i) {
                isCorrect = false;
              }
            }
            if (isCorrect) nextQuestion();
          }
        } else {
          const isCorrect = checkSpellingSentenceCorrect();
          if (isCorrect) {
            nextQuestion();
          }
        }
      }
    }
    // Letters A, B, C, D to answer (TOEIC Mode)
    else if (currentMode === "toeic" && !isToeicAnswered && 
             (e.key.toLowerCase() === "a" || e.key.toLowerCase() === "b" || 
              e.key.toLowerCase() === "c" || e.key.toLowerCase() === "d")) {
      e.preventDefault();
      selectToeicOption(e.key.toUpperCase());
    }
    // Numbers 1, 2, 3, 4 to answer (TOEIC Mode)
    else if (currentMode === "toeic" && !isToeicAnswered && 
             (e.key === "1" || e.key === "2" || e.key === "3" || e.key === "4")) {
      e.preventDefault();
      const optionLetters = ["A", "B", "C", "D"];
      const optIdx = parseInt(e.key, 10) - 1;
      selectToeicOption(optionLetters[optIdx]);
    }
    // Space key: Play/Pause Audio (TOEIC Part 2 Mode)
    else if (e.key === " " || e.code === "Space") {
      if (currentMode === "toeic-part2") {
        e.preventDefault();
        togglePart2Audio();
      }
    }
    // Letters A, B, C to answer (TOEIC Part 2 Mode)
    else if (currentMode === "toeic-part2" && !isPart2Answered && 
             (e.key.toLowerCase() === "a" || e.key.toLowerCase() === "b" || 
              e.key.toLowerCase() === "c")) {
      e.preventDefault();
      selectPart2Option(e.key.toUpperCase());
    }
    // Numbers 1, 2, 3 to answer (TOEIC Part 2 Mode)
    else if (currentMode === "toeic-part2" && !isPart2Answered && 
             (e.key === "1" || e.key === "2" || e.key === "3")) {
      e.preventDefault();
      const optionLetters = ["A", "B", "C"];
      const optIdx = parseInt(e.key, 10) - 1;
      selectPart2Option(optionLetters[optIdx]);
    }
    // Scramble Selection keys
    else if (currentMode === "sentence" && isScrambleMode && e.key >= "1" && e.key <= "9") {
      const optionIdx = parseInt(e.key, 10) - 1;
      const cards = scrambleOptions.querySelectorAll(".word-card");
      if (optionIdx < cards.length) {
        const targetCard = cards[optionIdx];
        if (!targetCard.classList.contains("selected")) {
          selectScrambleCard(targetCard);
        }
      }
    }
  });
}

// Run the app on DOM Load
window.addEventListener("DOMContentLoaded", init);
