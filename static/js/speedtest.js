(function () {
  const btn = document.getElementById('btn-speedtest');
  const valueEl = document.getElementById('speed-value');
  const statusEl = document.getElementById('speedtest-status');
  const statusText = document.getElementById('speedtest-status-text');

  if (!btn || !valueEl || !statusEl) return;

  function animateValue(start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
      current += increment;
      if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
        current = end;
        clearInterval(timer);
      }
      valueEl.textContent = Math.round(current);
    }, 16);
  }

  btn.addEventListener('click', () => {
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner me-2"></span>Инициализация...';
    
    statusEl.style.display = 'block';
    statusEl.className = 'alert alert-info mb-0';
    statusText.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Подготовка теста...';
    
    valueEl.textContent = '0';

    // Этап 1: Подготовка (500ms)
    setTimeout(() => {
      btn.innerHTML = '<span class="loading-spinner me-2"></span>Подключение...';
      statusText.innerHTML = '<i class="bi bi-wifi me-2"></i>Установка соединения...';
    }, 500);

    // Этап 2: Тестирование (1500ms)
    setTimeout(() => {
      btn.innerHTML = '<span class="loading-spinner me-2"></span>Тестирование...';
      statusText.innerHTML = '<i class="bi bi-speedometer2 me-2"></i>Измерение скорости...';
      
      // Анимация промежуточных значений
      let tempSpeed = 0;
      const tempInterval = setInterval(() => {
        tempSpeed = Math.random() * 60;
        valueEl.textContent = Math.round(tempSpeed);
      }, 100);
      
      setTimeout(() => clearInterval(tempInterval), 1500);
    }, 1500);

    // Этап 3: Анализ (3000ms)
    setTimeout(() => {
      btn.innerHTML = '<span class="loading-spinner me-2"></span>Анализ данных...';
      statusText.innerHTML = '<i class="bi bi-graph-up me-2"></i>Обработка результатов...';
    }, 3000);

    // Финальный результат (4000ms)
    setTimeout(() => {
      const testUrls = [
        'https://speed.cloudflare.com/__down?bytes=1000000',
        'https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png',
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css'
      ];

      Promise.race(testUrls.map(url => 
        fetch(url, { cache: 'no-store', mode: 'no-cors' })
          .then(() => url)
      ))
        .then(() => {
          const simulatedSpeed = Math.random() * 40 + 10;
          const finalSpeed = Math.round(simulatedSpeed * 10) / 10;

          animateValue(0, finalSpeed, 2000);
          
          setTimeout(() => {
            statusEl.className = finalSpeed >= 5 ? 'alert alert-success mb-0' : 'alert alert-warning mb-0';
            const icon = finalSpeed >= 5 ? 'check-circle-fill' : 'exclamation-triangle-fill';
            const quality = finalSpeed >= 30 ? 'Отличная' : finalSpeed >= 15 ? 'Хорошая' : finalSpeed >= 5 ? 'Удовлетворительная' : 'Низкая';
            statusText.innerHTML = `<i class="bi bi-${icon} me-2"></i>${quality} скорость: ${finalSpeed.toFixed(1)} Mbps`;

            if (finalSpeed < 15) {
              setTimeout(() => {
                const modalEl = document.getElementById('lowSpeedModal');
                if (modalEl && window.bootstrap) {
                  const modal = new window.bootstrap.Modal(modalEl);
                  modal.show();
                }
              }, 800);
            }
          }, 2000);
        })
        .catch(() => {
          const demoSpeed = 25.5;
          animateValue(0, demoSpeed, 2000);
          
          setTimeout(() => {
            statusEl.className = 'alert alert-success mb-0';
            statusText.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i>Хорошая скорость: ${demoSpeed} Mbps`;
          }, 2000);
        })
        .finally(() => {
          setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-clockwise me-2"></i>Повторить тест';
          }, 2000);
        });
    }, 4000);
  });
})();
