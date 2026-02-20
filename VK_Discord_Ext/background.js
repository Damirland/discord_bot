// Я - посредник. Я принимаю данные от вкладки ВК и легально отправляю их в Python!
chrome.runtime.onMessage.addListener((data, sender, sendResponse) => {
    fetch('http://127.0.0.1:8000', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).catch(err => console.error("❌ Ошибка сервера:", err));
    
    return true; 
});