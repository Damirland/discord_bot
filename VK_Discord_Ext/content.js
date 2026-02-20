console.log("Партнер Программиста: Активирован модуль спасения потерянных артистов!");

function cleanText(str) {
    if (!str) return "";
    return str.replace(/\s+/g, ' ').trim();
}

setInterval(() => {
    try {
        let titleEl = document.querySelector('[data-testid="audioplayeraudioinfo-title"]') 
                   || document.querySelector('[class*="AudioInfo__title"]');
                   
        let artistEl = document.querySelector('[data-testid="audio-player-block-audio-artists"]') 
                    || document.querySelector('[class*="AudioInfo__artists"]');

        // Если нет даже названия песни - тогда точно ничего не играет, прерываемся
        if (!titleEl) return;

        let cleanTitle = cleanText(titleEl.textContent);
        let cleanArtist = artistEl ? cleanText(artistEl.textContent) : "";

        // МАГИЯ СПАСЕНИЯ: Если ВК спрятал артиста
        if (!cleanArtist) {
            // Проверяем, не запихал ли ВК всё в одно название (например: "Сам - Noize mc")
            if (cleanTitle.includes(' - ')) {
                let parts = cleanTitle.split(' - ');
                // Берем первую часть как артиста, вторую как песню (или наоборот, зависит от формата ВК, обычно Артист - Песня)
                cleanArtist = parts[0].trim();
                cleanTitle = parts.slice(1).join(' - ').trim();
            } else {
                // Если дефиса нет, просто ставим заглушку, чтобы Discord не ругался
                cleanArtist = "Неизвестный исполнитель";
            }
        }

        let currentStr = "0:00";
        let timeEl = document.querySelector('[data-testid="audioplayerplaybackbody-progresstime"] span')
                  || document.querySelector('[class*="PlaybackProgressTime"] span');
        if (timeEl) currentStr = timeEl.textContent.trim();

        let progressPercent = 0;
        let progressContainer = document.querySelector('[data-testid="audio-player-block-progress-bar"]')
                             || document.querySelector('[class*="Progress"]');
        
        if (progressContainer) {
            let fills = progressContainer.querySelectorAll('div[class*="vkitSlider__fill"]');
            let validWidths = [];

            for (let el of fills) {
                let className = el.className || "";
                if (className.includes('Transparent') || className.includes('Background')) continue;

                if (el.style && el.style.width) {
                    let w = parseFloat(el.style.width);
                    if (!isNaN(w) && w > 0 && w <= 100) validWidths.push(w);
                }
            }
            if (validWidths.length > 0) progressPercent = Math.min(...validWidths);
        }

        let stateBtn = document.querySelector('[data-testid="audio-player-controls-state-button"]')
                    || document.querySelector('[class*="ControlsStateButton"]');
        let isPlaying = stateBtn ? stateBtn.textContent.includes("Приостановить") : false;

        let data = {
            title: cleanTitle,
            artist: cleanArtist,
            isPlaying: isPlaying,
            cover: document.querySelector('[data-testid="audioplayerplaybackbody-cover"] img')?.src || "",
            currentTime: currentStr,
            progress: progressPercent
        };

        chrome.runtime.sendMessage(data);

    } catch (e) {
        console.error("❌ ОШИБКА В JS:", e);
    }
}, 2000);