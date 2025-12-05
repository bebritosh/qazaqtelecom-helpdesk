// Система уведомлений для операторов
(function() {
  const badge = document.getElementById('notification-badge');
  
  if (!badge) return; // Если бейдж не найден (пользователь не оператор), выходим
  
  // Функция для получения уведомлений
  async function fetchNotifications() {
    try {
      const response = await fetch('/tickets/api/operator/notifications/');
      if (!response.ok) return;
      
      const data = await response.json();
      const count = data.unread_count || 0;
      
      if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline-block';
      } else {
        badge.style.display = 'none';
      }
    } catch (error) {
      console.error('Ошибка загрузки уведомлений:', error);
    }
  }
  
  // Загружаем уведомления при загрузке страницы
  fetchNotifications();
  
  // Обновляем каждые 10 секунд
  setInterval(fetchNotifications, 10000);
})();
