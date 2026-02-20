console.log("Бот ВК-Discord: Режим VKUI активен!");

setInterval(() => {
    try {
        // 1. Ищем название и артиста через data-testid (самый надежный способ)
        let titleEl = document.querySelector('[data-testid="audioplayeraudioinfo-title"]');
        let artistEl = document.querySelector('[data-testid="audio-player-block-audio-artists"]');

        if (titleEl && artistEl) {
            // 2. Проверяем, играет ли музыка
            // Если кнопка имеет текст "Приостановить" или иконку "pause", значит музыка играет
            let stateBtn = document.querySelector('[data-testid="audio-player-controls-state-button"]');
            let isPlaying = stateBtn ? stateBtn.innerText.includes("Приостановить") || !!document.querySelector('svg[class*="pause"]') : false;
            
            // 3. Обложка
            let coverEl = document.querySelector('[data-testid="audioplayerplaybackbody-cover"] img');
            let coverUrl = coverEl ? coverEl.src : "https://cdn-icons-png.flaticon.com/512/6028/6028590.png";

            // 4. ТЕКУЩЕЕ ВРЕМЯ
            let currentStr = "0:00";
            let timeEl = document.querySelector('[data-testid="audioplayerplaybackbody-progresstime"]');
            if (timeEl) {
                currentStr = timeEl.textContent.trim();
            }

            // 5. ОБЩЕЕ ВРЕМЯ (Хак: ищем его в списке песен, так как в плеере его может не быть)
            let totalStr = "0:00";
            // Ищем строку песни, которая сейчас подсвечена как "играющая"
            let playingRow = document.querySelector('.audio_row_playing');
            if (playingRow) {
                let durationEl = playingRow.querySelector('.audio_row__duration');
                if (durationEl) totalStr = durationEl.textContent.trim();
            }

            // Если в списке не нашли, пробуем найти любое время в плеере, которое не является текущим
            if (totalStr === "0:00") {
                let allTimes = Array.from(document.querySelectorAll('[class*="progressTime"], [class*="duration"]'))
                                    .map(el => el.textContent.trim())
                                    .filter(t => /^\d{1,2}:\d{2}$/.test(t) && t !== currentStr);
                if (allTimes.length > 0) totalStr = allTimes[0];
            }

            let data = {
                title: titleEl.textContent.trim(),
                artist: artistEl.textContent.trim(),
                isPlaying: isPlaying,
                cover: coverUrl,
                timeInfo: `[${currentStr} / ${totalStr}]`
            };

            // Отправляем данные в background.js
            chrome.runtime.sendMessage(data);
        }
    } catch (e) {
        console.error("Ошибка парсинга плеера:", e);
    }
}, 2000);