(function () {
  const messagesEl = document.getElementById('chat-messages');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const fileInput = document.getElementById('file-input');
  const btnVoice = document.getElementById('btn-voice');
  const filePreview = document.getElementById('file-preview');

  if (!messagesEl || !form || !input) return;

  function appendMessage(text, isBot, imageUrl = null, messageId = null, rating = null) {
    const wrapper = document.createElement('div');
    wrapper.className = 'd-flex mb-3 ' + (isBot ? '' : 'justify-content-end');

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble ' + (isBot ? 'msg-bot' : 'msg-user');
    
    if (imageUrl) {
      const img = document.createElement('img');
      img.src = imageUrl;
      img.className = 'img-fluid rounded mb-2';
      img.style.maxWidth = '200px';
      bubble.appendChild(img);
    }
    
    if (text) {
      const textNode = document.createElement('div');
      textNode.textContent = text;
      bubble.appendChild(textNode);
    }

    // Добавляем кнопки оценки для ответов AI
    if (isBot && messageId) {
      const ratingDiv = document.createElement('div');
      ratingDiv.className = 'mt-2 d-flex gap-2 align-items-center';
      ratingDiv.style.fontSize = '0.85rem';
      
      const helpfulBtn = document.createElement('button');
      helpfulBtn.className = 'btn btn-sm ' + (rating === 1 ? 'btn-success' : 'btn-outline-secondary');
      helpfulBtn.innerHTML = '👍 Полезно';
      helpfulBtn.onclick = () => rateMessage(messageId, 1, helpfulBtn, notHelpfulBtn);
      
      const notHelpfulBtn = document.createElement('button');
      notHelpfulBtn.className = 'btn btn-sm ' + (rating === -1 ? 'btn-danger' : 'btn-outline-secondary');
      notHelpfulBtn.innerHTML = '👎 Не помогло';
      notHelpfulBtn.onclick = () => rateMessage(messageId, -1, helpfulBtn, notHelpfulBtn);
      
      ratingDiv.appendChild(helpfulBtn);
      ratingDiv.appendChild(notHelpfulBtn);
      bubble.appendChild(ratingDiv);
    }

    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function rateMessage(messageId, rating, helpfulBtn, notHelpfulBtn) {
    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]');
    
    fetch('/tickets/api/chat/rate/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken ? csrfToken.value : ''
      },
      body: JSON.stringify({ message_id: messageId, rating: rating })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          // Обновляем стили кнопок
          if (rating === 1) {
            helpfulBtn.className = 'btn btn-sm btn-success';
            notHelpfulBtn.className = 'btn btn-sm btn-outline-secondary';
          } else {
            helpfulBtn.className = 'btn btn-sm btn-outline-secondary';
            notHelpfulBtn.className = 'btn btn-sm btn-danger';
          }
        }
      })
      .catch(err => console.error('Rating error:', err));
  }

  function showTypingIndicator() {
    const wrapper = document.createElement('div');
    wrapper.className = 'd-flex mb-3';
    wrapper.id = 'typing-indicator';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble msg-bot';
    bubble.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div><div class="typing-text" style="font-size: 0.85rem; color: rgba(255,255,255,0.7); margin-top: 0.5rem;">AI печатает...</div>';
    bubble.style.padding = '0.75rem 1.25rem';

    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
  }

  // Загрузка истории сообщений при открытии страницы
  function loadChatHistory() {
    fetch('/tickets/api/chat/history/', {
      method: 'GET',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then(res => res.json())
      .then(data => {
        if (data && data.messages && data.messages.length > 0) {
          // Загружаем существующие сообщения
          data.messages.forEach(msg => {
            appendMessage(msg.text, msg.is_bot, msg.image_url, msg.id, msg.rating);
          });
        } else {
          // Если истории нет, показываем приветствие
          appendMessage('Здравствуйте! Я ИИ-помощник Казахтелеком. Опишите вашу проблему, и я помогу найти решение.', true);
          // Показываем быстрые ответы для нового чата
          if (quickRepliesEl) quickRepliesEl.style.display = 'block';
        }
      })
      .catch(() => {
        // При ошибке показываем приветствие
        appendMessage('Здравствуйте! Я ИИ-помощник Казахтелеком. Опишите вашу проблему, и я помогу найти решение.', true);
      });
  }

  // Загружаем историю при открытии страницы
  loadChatHistory();

  // Быстрые ответы
  const quickRepliesEl = document.getElementById('quick-replies');
  const quickReplyBtns = document.querySelectorAll('.quick-reply-btn');
  
  // Показываем быстрые ответы только если чат пустой
  function checkQuickReplies() {
    const hasMessages = messagesEl.children.length > 1; // больше чем приветствие
    if (quickRepliesEl) {
      quickRepliesEl.style.display = hasMessages ? 'none' : 'block';
    }
  }
  
  quickReplyBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.getAttribute('data-text');
      if (text) {
        input.value = text;
        form.dispatchEvent(new Event('submit'));
        if (quickRepliesEl) quickRepliesEl.style.display = 'none';
      }
    });
  });

  // Статус "печатает..."
  let typingTimeout;
  input.addEventListener('input', () => {
    // Можно добавить отправку события "user is typing" на сервер
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
      // Пользователь перестал печатать
    }, 1000);
  });

  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          if (filePreview) {
            filePreview.innerHTML = `
              <div class="position-relative d-inline-block">
                <img src="${event.target.result}" class="img-thumbnail" style="max-width: 100px; max-height: 100px;">
                <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 rounded-circle" 
                        style="width: 24px; height: 24px; padding: 0;" onclick="this.parentElement.parentElement.innerHTML=''; document.getElementById('file-input').value='';">
                  <i class="bi bi-x"></i>
                </button>
              </div>
            `;
            filePreview.style.display = 'block';
          }
        };
        reader.readAsDataURL(file);
      }
    });
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    const hasFile = fileInput && fileInput.files[0];
    
    if (!text && !hasFile) return;

    let imagePreviewUrl = null;
    if (hasFile) {
      imagePreviewUrl = URL.createObjectURL(fileInput.files[0]);
    }

    appendMessage(text, false, imagePreviewUrl);
    input.value = '';
    if (filePreview) filePreview.style.display = 'none';

    showTypingIndicator();

    const formData = new FormData();
    formData.append('text', text);
    if (hasFile) {
      formData.append('image', fileInput.files[0]);
      fileInput.value = '';
    }

    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]');
    
    fetch('/tickets/api/chat/', {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken ? csrfToken.value : ''
      },
      body: formData,
    })
      .then(res => {
        if (!res.ok) throw new Error('Network error');
        return res.json();
      })
      .then(data => {
        hideTypingIndicator();
        if (data && data.reply) {
          setTimeout(() => appendMessage(data.reply, true, null, data.message_id, null), 300);
        }
      })
      .catch(() => {
        hideTypingIndicator();
        appendMessage('Произошла ошибка. Попробуйте ещё раз или обратитесь к оператору.', true);
      });
  });

  if (btnVoice && 'webkitSpeechRecognition' in window) {
    const Recognition = window.webkitSpeechRecognition;
    const recognition = new Recognition();
    recognition.lang = 'ru-RU';
    recognition.interimResults = false;

    btnVoice.addEventListener('click', () => {
      btnVoice.innerHTML = '<span class="loading-spinner"></span>';
      recognition.start();
    });

    recognition.addEventListener('result', (event) => {
      const transcript = event.results[0][0].transcript;
      input.value = transcript;
      input.focus();
      btnVoice.innerHTML = '<i class="bi bi-mic"></i>';
    });

    recognition.addEventListener('error', () => {
      btnVoice.innerHTML = '<i class="bi bi-mic"></i>';
    });

    recognition.addEventListener('end', () => {
      btnVoice.innerHTML = '<i class="bi bi-mic"></i>';
    });
  }

  const style = document.createElement('style');
  style.textContent = `
    .typing-dots { display: flex; gap: 4px; }
    .typing-dots span {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: rgba(255,255,255,0.7);
      animation: typing 1.4s infinite;
    }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typing {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.7; }
      30% { transform: translateY(-10px); opacity: 1; }
    }
  `;
  document.head.appendChild(style);
})();
