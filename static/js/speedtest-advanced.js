(function () {
  const speedtestSections = document.querySelectorAll('[data-speedtest-section]');
  
  speedtestSections.forEach(section => {
    const btn = section.querySelector('[data-speedtest-btn]');
    const canvas = section.querySelector('[data-speedtest-canvas]');
    const downloadEl = section.querySelector('[data-download]');
    const uploadEl = section.querySelector('[data-upload]');
    const pingEl = section.querySelector('[data-ping]');
    const statusEl = section.querySelector('[data-status]');

    if (!btn || !canvas) return;

    const ctx = canvas.getContext('2d');
    let animationFrame;
    let currentSpeed = 0;
    let targetSpeed = 0;

    // Настройка canvas
    function resizeCanvas() {
      const size = Math.min(canvas.parentElement.clientWidth, 300);
      canvas.width = size;
      canvas.height = size;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Рисование кругового индикатора
    function drawSpeedometer(speed, maxSpeed = 100) {
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const radius = Math.min(centerX, centerY) - 20;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Фоновая дуга
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, 2.25 * Math.PI);
      ctx.lineWidth = 20;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.stroke();

      // Градиент для активной дуги
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
      gradient.addColorStop(0, '#00AEEF');
      gradient.addColorStop(0.5, '#0099d6');
      gradient.addColorStop(1, '#0066ff');

      // Активная дуга (прогресс)
      const progress = Math.min(speed / maxSpeed, 1);
      const endAngle = 0.75 * Math.PI + progress * 1.5 * Math.PI;
      
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, endAngle);
      ctx.lineWidth = 20;
      ctx.lineCap = 'round';
      ctx.strokeStyle = gradient;
      ctx.stroke();

      // Центральное значение
      ctx.fillStyle = '#fff';
      ctx.font = `bold ${canvas.width * 0.15}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(Math.round(speed), centerX, centerY - 10);

      // Подпись Mbps
      ctx.font = `${canvas.width * 0.06}px Inter, sans-serif`;
      ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
      ctx.fillText('Mbps', centerX, centerY + 25);
    }

    // Анимация значения
    function animateSpeed() {
      const diff = targetSpeed - currentSpeed;
      if (Math.abs(diff) > 0.1) {
        currentSpeed += diff * 0.1;
        drawSpeedometer(currentSpeed);
        animationFrame = requestAnimationFrame(animateSpeed);
      } else {
        currentSpeed = targetSpeed;
        drawSpeedometer(currentSpeed);
      }
    }

    // Обновление метрик
    function updateMetrics(download, upload, ping) {
      if (downloadEl) downloadEl.textContent = download.toFixed(1);
      if (uploadEl) uploadEl.textContent = upload.toFixed(1);
      if (pingEl) pingEl.textContent = Math.round(ping);
    }

    // Симуляция теста
    function runSpeedtest() {
      btn.disabled = true;
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Тестирование...';

      if (statusEl) {
        statusEl.style.display = 'block';
        statusEl.textContent = 'Инициализация...';
      }

      // Сброс значений
      targetSpeed = 0;
      currentSpeed = 0;
      updateMetrics(0, 0, 0);
      drawSpeedometer(0);

      // Этап 1: Ping test (500ms)
      setTimeout(() => {
        const ping = Math.random() * 30 + 10;
        updateMetrics(0, 0, ping);
        if (statusEl) statusEl.textContent = 'Измерение задержки...';
      }, 500);

      // Этап 2: Download test (1500ms)
      setTimeout(() => {
        if (statusEl) statusEl.textContent = 'Тест загрузки...';
        
        // Анимация роста скорости
        let tempSpeed = 0;
        const downloadInterval = setInterval(() => {
          tempSpeed += Math.random() * 15;
          targetSpeed = Math.min(tempSpeed, 100);
          if (!animationFrame) animateSpeed();
        }, 100);

        setTimeout(() => {
          clearInterval(downloadInterval);
          const finalDownload = Math.random() * 60 + 20;
          targetSpeed = finalDownload;
          updateMetrics(finalDownload, 0, pingEl ? parseFloat(pingEl.textContent) : 15);
        }, 1500);
      }, 1500);

      // Этап 3: Upload test (3500ms)
      setTimeout(() => {
        if (statusEl) statusEl.textContent = 'Тест отдачи...';
        const upload = Math.random() * 30 + 10;
        updateMetrics(
          downloadEl ? parseFloat(downloadEl.textContent) : 50,
          upload,
          pingEl ? parseFloat(pingEl.textContent) : 15
        );
      }, 3500);

      // Завершение (5000ms)
      setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-arrow-clockwise me-2"></i>Повторить тест';
        
        if (statusEl) {
          const finalSpeed = downloadEl ? parseFloat(downloadEl.textContent) : 50;
          const quality = finalSpeed >= 30 ? 'Отличная' : finalSpeed >= 15 ? 'Хорошая' : 'Низкая';
          statusEl.textContent = `${quality} скорость соединения`;
          statusEl.style.color = finalSpeed >= 30 ? '#4caf50' : finalSpeed >= 15 ? '#00AEEF' : '#ff9800';
        }

        // Показать модалку при низкой скорости
        const finalSpeed = downloadEl ? parseFloat(downloadEl.textContent) : 50;
        if (finalSpeed < 15) {
          setTimeout(() => {
            const modalEl = document.getElementById('lowSpeedModal');
            if (modalEl && window.bootstrap) {
              const modal = new window.bootstrap.Modal(modalEl);
              modal.show();
            }
          }, 800);
        }
      }, 5000);
    }

    // Инициализация
    drawSpeedometer(0);
    btn.addEventListener('click', runSpeedtest);
  });

  // Поддержка маленькой карточки "Онлайн-диагностика" в hero-блоке
  const heroBtn = document.getElementById('btn-speedtest-hero');
  if (heroBtn) {
    heroBtn.addEventListener('click', () => {
      const section = document.querySelector('[data-speedtest-section]');
      if (!section) return;

      // Плавно прокручиваем к основному speedtest-блоку
      try {
        section.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } catch (e) {
        // старые браузеры без smooth
        section.scrollIntoView();
      }

      // Автоматически запускаем тест, если есть кнопка
      const mainBtn = section.querySelector('[data-speedtest-btn]');
      if (mainBtn && !mainBtn.disabled) {
        mainBtn.click();
      }
    });
  }
})();
