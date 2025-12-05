(function () {
  const searchInput = document.querySelector('input[placeholder*="Поиск"]') || document.querySelector('input[placeholder*="іздеу"]');
  const statusSelect = document.querySelectorAll('.form-select')[0];
  const categorySelect = document.querySelectorAll('.form-select')[1];
  const prioritySelect = document.querySelectorAll('.form-select')[2];
  const resetBtn = document.querySelector('.btn-outline-secondary');
  const tableRows = document.querySelectorAll('tbody tr');

  if (!searchInput || !tableRows.length) return;

  function filterTickets() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const statusFilter = statusSelect ? statusSelect.value : '';
    const categoryFilter = categorySelect ? categorySelect.value : '';
    const priorityFilter = prioritySelect ? prioritySelect.value : '';

    let visibleCount = 0;

    tableRows.forEach(row => {
      const ticketId = row.querySelector('td:first-child')?.textContent.toLowerCase() || '';
      const subject = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
      const client = row.querySelector('td:nth-child(3)')?.textContent.toLowerCase() || '';
      const category = row.querySelector('td:nth-child(5)')?.textContent.trim() || '';
      const priority = row.querySelector('td:nth-child(6)')?.textContent.trim() || '';
      const status = row.querySelector('td:nth-child(7)')?.textContent.trim() || '';

      // Поиск по ID, теме или клиенту
      const matchesSearch = !searchTerm || 
        ticketId.includes(searchTerm) || 
        subject.includes(searchTerm) ||
        client.includes(searchTerm);

      // Фильтр по статусу
      const matchesStatus = !statusFilter || 
        statusFilter.includes('Все') || 
        statusFilter.includes('Барлық') ||
        status.includes(statusFilter);

      // Фильтр по категории
      const matchesCategory = !categoryFilter || 
        categoryFilter.includes('Все') || 
        categoryFilter.includes('Барлық') ||
        category.includes(categoryFilter);

      // Фильтр по приоритету
      const matchesPriority = !priorityFilter || 
        priorityFilter.includes('Все') || 
        priorityFilter.includes('Барлық') ||
        priority.includes(priorityFilter);

      const isVisible = matchesSearch && matchesStatus && matchesCategory && matchesPriority;

      row.style.display = isVisible ? '' : 'none';
      if (isVisible) visibleCount++;
    });

    // Обновляем счётчик
    const counterEl = document.querySelector('.bi-ticket-detailed')?.parentElement;
    if (counterEl) {
      const totalText = counterEl.textContent.includes('тикетов') ? 'тикетов' : 'тикет';
      counterEl.innerHTML = `<i class="bi bi-ticket-detailed me-2"></i>${visibleCount} ${totalText}`;
    }
  }

  // Поиск в реальном времени
  searchInput.addEventListener('input', filterTickets);

  // Фильтры
  if (statusSelect) statusSelect.addEventListener('change', filterTickets);
  if (categorySelect) categorySelect.addEventListener('change', filterTickets);
  if (prioritySelect) prioritySelect.addEventListener('change', filterTickets);

  // Сброс фильтров
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      searchInput.value = '';
      if (statusSelect) statusSelect.selectedIndex = 0;
      if (categorySelect) categorySelect.selectedIndex = 0;
      if (prioritySelect) prioritySelect.selectedIndex = 0;
      filterTickets();
    });
  }

  // Подсветка найденного текста
  searchInput.addEventListener('input', () => {
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    tableRows.forEach(row => {
      const cells = row.querySelectorAll('td');
      cells.forEach(cell => {
        const originalText = cell.getAttribute('data-original-text') || cell.textContent;
        if (!cell.getAttribute('data-original-text')) {
          cell.setAttribute('data-original-text', originalText);
        }

        if (searchTerm && originalText.toLowerCase().includes(searchTerm)) {
          const regex = new RegExp(`(${searchTerm})`, 'gi');
          const highlighted = originalText.replace(regex, '<mark style="background-color: #fff3cd; padding: 0.1rem 0.2rem; border-radius: 2px;">$1</mark>');
          cell.innerHTML = highlighted;
        } else {
          cell.textContent = originalText;
        }
      });
    });
  });
})();
