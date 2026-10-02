// SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
// SPDX-License-Identifier: GPL-3.0-or-later

(() => {
  "use strict";
  const ASSETS = [
    {name: "IPLDUMP.BIN", source: "IPLDUMP.BIN", size: 4096},
    {name: "HD0_256.hda", source: "HD0_256.hda.gz", size: 10 * 1024 * 1024,
      compression: "gzip"},
    {name: "HD1_256.hda", source: "HD1_256.hda.gz", size: 10 * 1024 * 1024,
      compression: "gzip"},
  ];
  const FONT_ASSET = "p2000c-font.png";
  const DISPLAY_SCALE = 2;
  const CHARACTER_WIDTH = 8;
  const CHARACTER_HEIGHT = 12;
  const CHARACTER_SHEET_PITCH = 12;
  const GRAPHIC_WIDTH = 512;
  const GRAPHIC_HEIGHT = 252;
  const GRAPHIC_BYTES_PER_LINE = 64;
  const INVERTED_GRAPHIC_INTENSITY = [0x01, 0x00, 0x41, 0x40];
  const TRANSLATIONS = {
    nl: {
      pageTitle: "P2000C Navigator — browseremulator",
      pageDescription: "Gebruik de Philips P2000C Navigator-distributie in uw browser.",
      homeLabel: "P2000C Navigator-startpagina",
      projectLinks: "Projectlinks",
      source: "BRONCODE",
      download: "DOWNLOAD",
      gallery: "GALERIJ",
      galleryTitle: "De Philips P2000C in beeld",
      galleryPrevious: "Vorige foto",
      galleryNext: "Volgende foto",
      galleryChoose: "Kies een foto",
      galleryPhoto: "Foto {number}",
      galleryHint: "← / → bladeren",
      galleryCaption: "{number} / {total} · {caption}",
      photoNavigator: "P2000C Navigator op de Philips P2000C",
      photoMinesweeper: "Mijnenveger op de Philips P2000C",
      photoKakuro: "Kakuro op het originele groene beeldscherm",
      photoChessTitle: "Het startscherm van Schaken",
      photoChess: "Schaken op de Philips P2000C",
      photoZork: "Zork I op de Philips P2000C",
      emulatorStatus: "Emulatorstatus",
      machineLabel: "Philips P2000C-emulator",
      terminalLabel: "Interactief P2000C-scherm",
      canvasLabel: "P2000C-scherm met de originele 8 bij 12 tekengenerator",
      speed: "Snelheid",
      speedOriginal: "1× origineel",
      speedTurbo4: "4× turbo",
      speedTurbo8: "8× turbo",
      reset: "RESET",
      aboutTitle: "P2000C-webemulator",
      aboutBody: "Dit is een webemulator van de Philips P2000C. De emulator draait " +
        "P2000C Navigator en de meegeleverde CP/M-software volledig in uw browser.",
      controlsBody: "Klik op het scherm om uw toetsenbord te gebruiken. Gebruik " +
        "<strong>↑/↓</strong> om te kiezen, <strong>→</strong> of <strong>Enter</strong> " +
        "om te openen en <strong>←</strong> om terug te gaan. Met <strong>H</strong> " +
        "opent u de hulp, met <strong>S</strong> start u de schermbeveiliging en met " +
        "<strong>Q</strong> sluit u af naar CP/M. Met Reset start u de geëmuleerde computer opnieuw.",
      distribution: "P2000C SASI-DISTRIBUTIE",
      museum: "GEMAAKT VOOR HET HOME COMPUTER MUSEUM",
      languageToggle: "Taal: Nederlands. Schakel naar Engels.",
      loadingEmulator: "Emulator laden…",
      loadingAsset: "{name} LADEN…",
      loadingCharacterGenerator: "P2000C-TEKENGENERATOR LADEN…",
      initializingWasm: "WEBASSEMBLY INITIALISEREN…",
      mountingDrives: "SASI-SCHIJVEN KOPPELEN…",
      booting: "PHILIPS P2000C OPSTARTEN…",
      running: "Actief · klik op het scherm voor toetsenbordinvoer",
      machineReset: "Machine gereset. Opstarten vanaf SASI…",
      emulatorError: "EMULATORFOUT: {error}",
      emulatorFailed: "De browseremulator kon niet worden gestart.",
      loaderUnavailable: "WebAssembly-lader niet beschikbaar",
      decompressorUnavailable: "Deze browser kan de gecomprimeerde SASI-schijven niet uitpakken",
      characterGeneratorUnavailable: "De P2000C-tekengenerator kon niet worden geladen",
      characterGeneratorSize: "De P2000C-tekengenerator moet 192 bij 192 pixels zijn",
      sizeMismatch: "{name}: verwacht {expected} bytes, ontvangen {received}",
    },
    en: {
      pageTitle: "P2000C Navigator — browser emulator",
      pageDescription: "Run the Philips P2000C Navigator distribution in your browser.",
      homeLabel: "P2000C Navigator home",
      projectLinks: "Project links",
      source: "SOURCE",
      download: "DOWNLOAD",
      gallery: "GALLERY",
      galleryTitle: "The Philips P2000C in pictures",
      galleryPrevious: "Previous photo",
      galleryNext: "Next photo",
      galleryChoose: "Choose a photo",
      galleryPhoto: "Photo {number}",
      galleryHint: "← / → browse",
      galleryCaption: "{number} / {total} · {caption}",
      photoNavigator: "P2000C Navigator on the Philips P2000C",
      photoMinesweeper: "Minesweeper on the Philips P2000C",
      photoKakuro: "Kakuro on the original green display",
      photoChessTitle: "The Chess title screen",
      photoChess: "Chess on the Philips P2000C",
      photoZork: "Zork I on the Philips P2000C",
      emulatorStatus: "Emulator status",
      terminalLabel: "Interactive P2000C display",
      machineLabel: "Philips P2000C emulator",
      canvasLabel: "P2000C display rendered with the original 8 by 12 character generator",
      speed: "Speed",
      speedOriginal: "1× original",
      speedTurbo4: "4× turbo",
      speedTurbo8: "8× turbo",
      reset: "RESET",
      aboutTitle: "P2000C web emulator",
      aboutBody: "This is a web-based emulator of the Philips P2000C. It runs P2000C " +
        "Navigator and its bundled CP/M software entirely in your browser.",
      controlsBody: "Click the screen to use your keyboard. Use <strong>↑/↓</strong> to " +
        "choose, <strong>→</strong> or <strong>Enter</strong> to open, and " +
        "<strong>←</strong> to go back. <strong>H</strong> opens help, " +
        "<strong>S</strong> starts the screen saver, and <strong>Q</strong> " +
        "quits to CP/M. Reset restarts the emulated computer.",
      distribution: "P2000C SASI DISTRIBUTION",
      museum: "BUILT FOR THE HOME COMPUTER MUSEUM",
      languageToggle: "Language: English. Switch to Dutch.",
      loadingEmulator: "Loading emulator…",
      loadingAsset: "LOADING {name}…",
      loadingCharacterGenerator: "LOADING P2000C CHARACTER GENERATOR…",
      initializingWasm: "INITIALISING WEBASSEMBLY…",
      mountingDrives: "MOUNTING SASI DRIVES…",
      booting: "BOOTING PHILIPS P2000C…",
      running: "Running · click the display for keyboard input",
      machineReset: "Machine reset. Booting from SASI…",
      emulatorError: "EMULATOR ERROR: {error}",
      emulatorFailed: "Could not start the browser emulator.",
      loaderUnavailable: "WebAssembly loader unavailable",
      decompressorUnavailable: "This browser cannot decompress the SASI disk images",
      characterGeneratorUnavailable: "Could not load the P2000C character generator",
      characterGeneratorSize: "P2000C character generator must be 192 by 192 pixels",
      sizeMismatch: "{name}: expected {expected} bytes, received {received}",
    },
  };
  const LANGUAGE_STORAGE_KEY = "p2000c-language";
  const terminal = document.querySelector("#terminal");
  const displayScreen = document.querySelector("#display-screen");
  const displayContext = displayScreen.getContext("2d", {alpha: false});
  const rasterScreen = document.createElement("canvas");
  const rasterContext = rasterScreen.getContext("2d", {alpha: false});

  const loading = document.querySelector("#loading");
  const loadingMessage = document.querySelector("#loading-message");
  const loadingProgress = document.querySelector("#loading-progress");
  const status = document.querySelector("#status");
  const powerLight = document.querySelector("#power-light");
  const diskLight = document.querySelector("#disk-light");
  const speed = document.querySelector("#speed");
  const languageToggle = document.querySelector("#language-toggle");
  const gallery = document.querySelector("#gallery");
  const galleryImage = document.querySelector("#gallery-image");
  const galleryCaption = document.querySelector("#gallery-caption");
  const galleryPositions = document.querySelector("#gallery-positions");
  const photos = [
    {file: "navigator", caption: "photoNavigator"},
    {file: "minesweeper", caption: "photoMinesweeper"},
    {file: "kakuro", caption: "photoKakuro"},
    {file: "chess-title", caption: "photoChessTitle"},
    {file: "chess", caption: "photoChess"},
    {file: "zork", caption: "photoZork"},
  ];
  let photoIndex = 0;
  let language = "nl";
  let statusState = {key: "loadingEmulator", values: {}};
  let loadingState = {key: "initializingWasm", values: {}};
  let emulator = null;
  let characterDots = null;
  let running = false;
  let previousTime = 0;
  let previousRevision = -1;
  let previousCursorPhase = null;
  let previousAttributeBlinkPhase = null;
  let cursorPhase = true;
  let attributeBlinkPhase = true;
  let diskFlashTimer = 0;

  function savedLanguage() {
    try {
      return localStorage.getItem(LANGUAGE_STORAGE_KEY) === "en" ? "en" : "nl";
    } catch (_error) {
      return "nl";
    }
  }

  function storeLanguage() {
    try {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    } catch (_error) {
      // The toggle still works when browser storage is disabled.
    }
  }

  function text(key, values = {}) {
    return TRANSLATIONS[language][key].replace(
      /\{([a-z]+)\}/gi,
      (_match, name) => String(values[name] ?? "")
    );
  }

  function setStatus(key, values = {}) {
    statusState = {key, values};
    status.textContent = text(key, values);
  }

  function message(key, progress, values = {}) {
    loadingState = {key, values};
    loadingMessage.textContent = text(key, values);
    loadingProgress.style.width = Math.max(2, progress) + "%";
    setStatus(key, values);
  }

  function applyLanguage(nextLanguage, persist = false) {
    language = nextLanguage === "en" ? "en" : "nl";
    document.documentElement.lang = language;
    document.title = text("pageTitle");
    document.querySelector("#page-description").content = text("pageDescription");
    document.querySelectorAll("[data-i18n]").forEach(element => {
      element.textContent = text(element.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-html]").forEach(element => {
      element.innerHTML = text(element.dataset.i18nHtml);
    });
    document.querySelectorAll("[data-i18n-aria-label]").forEach(element => {
      element.setAttribute("aria-label", text(element.dataset.i18nAriaLabel));
    });
    updateGallery(false);
    languageToggle.setAttribute("aria-checked", language === "en" ? "true" : "false");
    languageToggle.setAttribute("aria-label", text("languageToggle"));
    loadingMessage.textContent = text(loadingState.key, loadingState.values);
    status.textContent = text(statusState.key, statusState.values);
    if (persist) storeLanguage();
  }

  languageToggle.addEventListener("click", () => {
    applyLanguage(language === "nl" ? "en" : "nl", true);
  });
  function updateGallery(loadImage = true) {
    const photo = photos[photoIndex];
    if (loadImage) {
      galleryImage.srcset = `gallery/${photo.file}-768.webp 768w, gallery/${photo.file}.webp 1448w`;
      galleryImage.sizes = "(max-width: 1060px) calc(100vw - 3rem), 1018px";
      galleryImage.src = `gallery/${photo.file}.webp`;
    }
    galleryImage.alt = text(photo.caption);
    galleryCaption.textContent = text("galleryCaption", {
      number: photoIndex + 1, total: photos.length, caption: text(photo.caption),
    });
    [...galleryPositions.children].forEach((button, index) => {
      button.setAttribute("aria-pressed", String(index === photoIndex));
      button.setAttribute("aria-label", text("galleryPhoto", {number: index + 1}));
    });
  }

  function cyclePhoto(direction) {
    photoIndex = (photoIndex + direction + photos.length) % photos.length;
    updateGallery();
  }

  photos.forEach((_photo, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = String(index + 1).padStart(2, "0");
    button.addEventListener("click", () => {
      photoIndex = index;
      updateGallery();
    });
    galleryPositions.append(button);
  });
  document.querySelector("#gallery-previous").addEventListener("click", () => cyclePhoto(-1));
  document.querySelector("#gallery-next").addEventListener("click", () => cyclePhoto(1));
  gallery.addEventListener("keydown", event => {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      cyclePhoto(event.key === "ArrowLeft" ? -1 : 1);
    }
  });
  let swipeStart = null;
  galleryImage.addEventListener("pointerdown", event => {
    if (event.pointerType === "touch") swipeStart = event.clientX;
  });
  galleryImage.addEventListener("pointerup", event => {
    if (swipeStart !== null && Math.abs(event.clientX - swipeStart) > 50) {
      cyclePhoto(event.clientX < swipeStart ? 1 : -1);
    }
    swipeStart = null;
  });
  galleryImage.addEventListener("pointercancel", () => { swipeStart = null; });
  applyLanguage(savedLanguage());
  updateGallery();

  async function download(asset, index) {
    message("loadingAsset", 10 + index * 24, {name: asset.name});
    const response = await fetch(asset.source);
    if (!response.ok) throw new Error(asset.source + ": HTTP " + response.status);
    let body = response.body;
    if (asset.compression) {
      if (typeof DecompressionStream !== "function") {
        throw new Error(text("decompressorUnavailable"));
      }
      body = body.pipeThrough(new DecompressionStream(asset.compression));
    }
    const bytes = new Uint8Array(await new Response(body).arrayBuffer());
    if (bytes.length !== asset.size) {
      throw new Error(text("sizeMismatch", {
        name: asset.name, expected: asset.size, received: bytes.length,
      }));
    }
    return bytes;
  }

  async function loadCharacterGenerator() {
    const image = new Image();
    const loaded = new Promise((resolve, reject) => {
      image.addEventListener("load", resolve, {once: true});
      image.addEventListener("error", () => reject(
        new Error(text("characterGeneratorUnavailable"))
      ), {once: true});
    });
    image.src = FONT_ASSET;
    await loaded;
    if (image.naturalWidth !== 192 || image.naturalHeight !== 192) {
      throw new Error(text("characterGeneratorSize"));
    }
    const sheet = document.createElement("canvas");
    sheet.width = image.naturalWidth;
    sheet.height = image.naturalHeight;
    const context = sheet.getContext("2d", {willReadFrequently: true});
    context.drawImage(image, 0, 0);
    const pixels = context.getImageData(0, 0, sheet.width, sheet.height).data;
    characterDots = new Uint8Array(256 * CHARACTER_WIDTH * CHARACTER_HEIGHT);
    for (let character = 0; character < 256; character += 1) {
      const left = (character & 0x0f) * CHARACTER_SHEET_PITCH;
      const top = (character >> 4) * CHARACTER_SHEET_PITCH;
      for (let y = 0; y < CHARACTER_HEIGHT; y += 1) {
        for (let x = 0; x < CHARACTER_WIDTH; x += 1) {
          const source = ((top + y) * sheet.width + left + x) * 4;
          characterDots[character * 96 + y * CHARACTER_WIDTH + x] =
            pixels[source + 1] === 0 ? 0 : 1;
        }
      }
    }
  }

  function glyphDot(character, x, y) {
    return characterDots[character * 96 + y * CHARACTER_WIDTH + x] !== 0;
  }

  function setPixel(pixels, offset, attribute) {
    if (attribute < 0) {
      pixels[offset] = 0;
      pixels[offset + 1] = 4;
      pixels[offset + 2] = 3;
      pixels[offset + 3] = 255;
      return;
    }
    const intensity = ((attribute & 0x40) !== 0 ? 2 : 0) |
      ((attribute & 0x01) !== 0 ? 1 : 0);
    // P2000C serial attributes: quarter, bold, normal, and half bright.
    const scale = [0.19, 1.0, 0.93, 0.47][intensity];
    pixels[offset] = Math.round(97 * scale);
    pixels[offset + 1] = Math.round(255 * scale);
    pixels[offset + 2] = Math.round(199 * scale);
    pixels[offset + 3] = 255;
  }

  function presentRaster(image, width, height) {
    rasterScreen.width = width;
    rasterScreen.height = height;
    rasterContext.putImageData(image, 0, 0);
    displayScreen.width = width * DISPLAY_SCALE;
    displayScreen.height = height * DISPLAY_SCALE;
    displayContext.imageSmoothingEnabled = false;
    displayContext.drawImage(
      rasterScreen, 0, 0, displayScreen.width, displayScreen.height
    );
  }

  function renderTextMode(screen, attributes, cursorPosition, cursorVisible) {
    const width = 80 * CHARACTER_WIDTH;
    const height = 24 * CHARACTER_HEIGHT;
    displayScreen.classList.remove("graphics-mode");
    const image = rasterContext.createImageData(width, height);
    for (let y = 0; y < height; y += 1) {
      const row = Math.floor(y / CHARACTER_HEIGHT);
      const glyphY = y % CHARACTER_HEIGHT;
      for (let x = 0; x < width; x += 1) {
        const column = Math.floor(x / CHARACTER_WIDTH);
        const position = row * 80 + column;
        const attribute = attributes[position];
        let dot = glyphDot(screen[position], x % CHARACTER_WIDTH, glyphY);
        if ((attribute & 0x20) !== 0 && glyphY === 9) dot = true;
        if ((attribute & 0x10) !== 0) dot = !dot;
        if ((attribute & 0x02) !== 0 && !attributeBlinkPhase) dot = false;
        let pixelAttribute = dot ? attribute : -1;
        if (cursorVisible && cursorPhase && position === cursorPosition) {
          pixelAttribute = 0x40;
        }
        setPixel(image.data, (y * width + x) * 4, pixelAttribute);
      }
    }
    presentRaster(image, width, height);
  }

  function graphicAttribute(mode, x, y, graphics) {
    const address = y * GRAPHIC_BYTES_PER_LINE;
    if (mode === 2) {
      const value = graphics[address + Math.floor(x / 8)];
      return (value & (0x80 >> (x & 7))) !== 0 ? 0x40 : 0;
    }
    const logicalX = Math.floor(x / 2);
    const value = graphics[address + Math.floor(logicalX / 4)];
    const pixel = logicalX & 3;
    const high = (value & (0x80 >> pixel)) !== 0;
    const low = (value & (0x08 >> pixel)) !== 0;
    if (!high && !low) return 0;
    if (high && low) return 0x01;
    return high ? 0x40 : 0x41;
  }

  function renderGraphicsMode(mode, screen, graphics, cursorPosition, cursorVisible) {
    displayScreen.classList.add("graphics-mode");
    const image = rasterContext.createImageData(GRAPHIC_WIDTH, GRAPHIC_HEIGHT);
    for (let y = 0; y < GRAPHIC_HEIGHT; y += 1) {
      const characterRow = Math.floor(y / CHARACTER_HEIGHT);
      const glyphY = y % CHARACTER_HEIGHT;
      for (let x = 0; x < GRAPHIC_WIDTH; x += 1) {
        const position = characterRow * 64 + Math.floor(x / CHARACTER_WIDTH);
        let attribute = graphicAttribute(mode, x, y, graphics);
        if (glyphDot(screen[position], x % CHARACTER_WIDTH, glyphY)) {
          if (mode === 2) {
            attribute = attribute === 0 ? 0x40 : 0;
          } else {
            const intensity = ((attribute & 0x40) !== 0 ? 2 : 0) |
              ((attribute & 0x01) !== 0 ? 1 : 0);
            attribute = INVERTED_GRAPHIC_INTENSITY[intensity];
          }
        }
        if (cursorVisible && cursorPhase && position === cursorPosition) {
          attribute = 0x40;
        }
        setPixel(
          image.data, (y * GRAPHIC_WIDTH + x) * 4,
          attribute === 0 ? -1 : attribute
        );
      }
    }
    presentRaster(image, GRAPHIC_WIDTH, GRAPHIC_HEIGHT);
  }

  function render() {
    const screenPointer = emulator._p2000c_screen();
    const attributePointer = emulator._p2000c_attributes();
    if (!screenPointer || !attributePointer || !characterDots) return;
    const mode = emulator._p2000c_graphics_mode();
    const columns = mode === 0 ? 80 : 64;
    const rows = mode === 0 ? 24 : 21;
    const screen = emulator.HEAPU8.subarray(
      screenPointer, screenPointer + columns * rows
    );
    const cursorPosition = emulator._p2000c_cursor_row() * columns +
      emulator._p2000c_cursor_column();
    const cursorVisible = emulator._p2000c_cursor_visible() !== 0;
    if (mode === 0) {
      const attributes = emulator.HEAPU8.subarray(
        attributePointer, attributePointer + columns * rows
      );
      renderTextMode(screen, attributes, cursorPosition, cursorVisible);
      return;
    }
    const graphicPointer = emulator._p2000c_graphics();
    if (!graphicPointer) return;
    const graphics = emulator.HEAPU8.subarray(
      graphicPointer, graphicPointer + GRAPHIC_BYTES_PER_LINE * GRAPHIC_HEIGHT
    );
    renderGraphicsMode(mode, screen, graphics, cursorPosition, cursorVisible);
  }

  function tick(time) {
    if (!running) return;
    const elapsed = previousTime ? Math.min(time - previousTime, 50) : 16;
    previousTime = time;
    const multiplier = Number(speed.value);
    let cycles = Math.max(20000, Math.floor(elapsed * 4000 * multiplier));
    while (cycles > 0) {
      const slice = Math.min(cycles, 250000);
      emulator._p2000c_run(slice);
      cycles -= slice;
    }
    const revision = emulator._p2000c_revision();
    const nextCursorPhase = Math.floor(time / 500) % 2 === 0;
    const nextAttributeBlinkPhase = Math.floor(time / 667) % 2 === 0;
    const screenChanged = revision !== previousRevision;
    const phaseChanged = nextCursorPhase !== previousCursorPhase ||
      nextAttributeBlinkPhase !== previousAttributeBlinkPhase;
    cursorPhase = nextCursorPhase;
    attributeBlinkPhase = nextAttributeBlinkPhase;
    if (screenChanged || phaseChanged) {
      previousRevision = revision;
      previousCursorPhase = cursorPhase;
      previousAttributeBlinkPhase = attributeBlinkPhase;
      render();
    }
    if (screenChanged) {
      diskLight.classList.add("on");
      clearTimeout(diskFlashTimer);
      diskFlashTimer = setTimeout(() => diskLight.classList.remove("on"), 70);
    }
    requestAnimationFrame(tick);
  }

  function queueKey(value) {
    if (!running) return;
    emulator._p2000c_key(value);
    terminal.focus();
  }

  terminal.addEventListener("keydown", event => {
    const special = {
      ArrowUp: 0x05, ArrowDown: 0x18, ArrowLeft: 0x13, ArrowRight: 0x04,
      Enter: 0x0d, Escape: 0x1b, Backspace: 0x08, Tab: 0x09,
    };
    let value = special[event.key];
    if (value === undefined && event.key.length === 1) value = event.key.charCodeAt(0);
    if (value !== undefined && value <= 0xff) {
      event.preventDefault();
      queueKey(value);
    }
  });
  document.querySelector("#reset").addEventListener("click", () => {
    if (!running) return;
    emulator._p2000c_reset();
    previousRevision = -1;
    setStatus("machineReset");
    terminal.focus();
  });

  async function start() {
    try {
      if (typeof createP2000C !== "function") throw new Error(text("loaderUnavailable"));
      message("loadingCharacterGenerator", 2);
      await loadCharacterGenerator();
      message("initializingWasm", 4);
      emulator = await createP2000C({
        locateFile: path => path,
        printErr: text => console.error(text),
      });
      const assets = [];
      for (let index = 0; index < ASSETS.length; index += 1) {
        const asset = ASSETS[index];
        assets.push([asset.name, await download(asset, index)]);
      }
      message("mountingDrives", 88);
      for (const asset of assets) emulator.FS.writeFile("/" + asset[0], asset[1]);
      if (!emulator._p2000c_init()) {
        throw new Error(emulator.UTF8ToString(emulator._p2000c_last_error()));
      }
      message("booting", 100);
      loading.hidden = true;
      powerLight.classList.add("on");
      setStatus("running");
      running = true;
      if (document.activeElement === document.body && location.hash !== "#gallery") {
        terminal.focus();
      }
      requestAnimationFrame(tick);
    } catch (error) {
      console.error(error);
      message("emulatorError", 100, {error: error.message});
      loadingProgress.style.background = "#ff655f";
      setStatus("emulatorFailed");
    }
  }
  start();
})();
