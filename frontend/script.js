// Константы для работы с календарем
const DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
const DAYS_SHORT = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
const START_HOUR = 8;
const END_HOUR = 20;
const HOUR_HEIGHT = 60;

// Получаем элементы страницы
const loginBtn = document.getElementById('login-btn');
const scheduleDiv = document.getElementById('schedule');

// Проверяем, есть ли в адресной строке параметры от Яндекса (?user_id=...)
const urlParams = new URLSearchParams(window.location.search);
const userId = urlParams.get('user_id');
const firstName = urlParams.get('first_name') || 'Студент';
const lastName = urlParams.get('last_name') || '';

// Если user_id есть, значит мы вернулись с авторизации
if (userId) {
    loginBtn.classList.add('hidden');       
    scheduleDiv.classList.remove('hidden'); 
    loadSchedule(userId, firstName, lastName); 
} else {
    // Если user_id нет, значит пользователь не вошел
    loginBtn.addEventListener('click', () => {
        window.location.href = '/auth/yandex'; // Отправляем на Яндекс
    });
}

async function loadSchedule(userId, firstName, lastName) {
    // Формируем URL для запроса с именем и фамилией
    const apiUrl = `http://localhost:8000/api/schedule/${userId}?first_name=${firstName}&last_name=${lastName}`;

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        if (!data || data.length === 0) {
            scheduleDiv.innerHTML = '<div class="empty-message">Нет данных для отображения</div>';
            return;
        }

        renderSchedule(data, scheduleDiv);
    } catch (error) {
        scheduleDiv.innerHTML = '<div class="empty-message">Ошибка загрузки расписания</div>';
        console.error(error);
    }
}

function renderSchedule(data, container) {
    container.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'schedule-grid';

    const emptyHeader = document.createElement('div');
    emptyHeader.className = 'day-header';
    grid.appendChild(emptyHeader);

    for (let i = 0; i < DAYS.length; i++) {
        const header = document.createElement('div');
        header.className = 'day-header';
        header.textContent = DAYS_SHORT[i];
        grid.appendChild(header);
    }

    const timeColumn = document.createElement('div');
    timeColumn.className = 'time-column';

    for (let hour = START_HOUR; hour < END_HOUR; hour++) {
        const slot = document.createElement('div');
        slot.className = 'time-slot';
        slot.textContent = `${String(hour).padStart(2, '0')}:00`;
        timeColumn.appendChild(slot);
    }
    grid.appendChild(timeColumn);

    const dayColumns = [];
    for (let i = 0; i < DAYS.length; i++) {
        const column = document.createElement('div');
        column.className = 'day-column';
        for (let hour = START_HOUR; hour < END_HOUR; hour++) {
            const cell = document.createElement('div');
            cell.className = 'hour-cell';
            column.appendChild(cell);
        }
        grid.appendChild(column);
        dayColumns.push(column);
    }
    container.appendChild(grid);

    data.forEach(item => {
        const dayIndex = DAYS.indexOf(item.day_of_week);
        if (dayIndex === -1) return;

        const top = timeToPixels(item.start_time);
        const height = durationToPixels(item.start_time, item.end_time);

        const event = document.createElement('div');
        event.className = 'event';
        event.style.top = top + 'px';
        event.style.height = height + 'px';

        event.innerHTML = `
            <div class="subject">${item.subject}</div>
            <div class="room">${item.room}</div>
            <div class="teacher">${item.teacher}</div>
        `;
        dayColumns[dayIndex].appendChild(event);
    });
}

function timeToPixels(time) {
    const [hours, minutes] = time.split(':').map(Number);
    return (hours - START_HOUR) * HOUR_HEIGHT + (minutes / 60) * HOUR_HEIGHT;
}

function durationToPixels(start, end) {
    const [startH, startM] = start.split(':').map(Number);
    const [endH, endM] = end.split(':').map(Number);
    const durationMinutes = (endH * 60 + endM) - (startH * 60 + startM);
    return (durationMinutes / 60) * HOUR_HEIGHT;
}

