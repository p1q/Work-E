# Інтеграція LinkedIn OAuth - Frontend

---

- **Авторизаційний URL LinkedIn**: `https://www.linkedin.com/oauth/v2/authorization`
- **Callback-URL на бекенді**: `https://wq.work.gd/api/users/linkedin/callback/`

## 2. Додати маршрут у фронтенді

У вашому роутері (React Router, Vue Router тощо) додайте новий маршрут для обробки результату авторизації:

```jsx
// React Router приклад
<Routes>
  {/* ...інші маршрути... */}
  <Route path="/linkedin-success" element={<LinkedInSuccess />} />
</Routes>
```

## 3. Створити компонент LinkedInSuccess

Компонент повинен:

1. Зчитати з URL параметр `token`.
2. Зберегти його (наприклад, у `localStorage` або Context).
3. За потреби виконати запит на отримання профілю користувача.
4. Перенаправити користувача на потрібну сторінку (дешборд, профіль тощо).

```jsx
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function LinkedInSuccess() {
  const navigate = useNavigate();
  const { search } = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(search);
    const token = params.get('token');

    if (token) {
      // Зберігаємо токен
      localStorage.setItem('authToken', token);

      // При потребі: fetch('/api/users/me/', { headers: { Authorization: `Token ${token}` } })

      // Редирект
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  }, [search, navigate]);

  return (
    <div style={{ textAlign: 'center', marginTop: '2rem' }}>
      <h2>Успішна авторизація через LinkedIn!</h2>
      <p>Зачекайте, йде перенаправлення...</p>
    </div>
  );
}
```

## 4. Ініціалізація OAuth запиту

При натисканні кнопки "Увійти через LinkedIn" викликайте авторизаційний запит:

```js
const clientId = 'ваш LINKEDIN_CLIENT_ID';
const redirectUri = 'https://wq.work.gd/api/users/linkedin/callback/';
const state = 'from-login';
const scope = 'r_liteprofile r_emailaddress';

const authUrl = `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&state=${state}&scope=${encodeURIComponent(scope)}`;

window.location.href = authUrl;
```

> **Примітка**: Використовуємо бекендний callback, щоб обмінювати код на токен на сервері (безпечніше).

## 5. Обробка скасування авторизації

Якщо користувач натисне "Cancel", LinkedIn покаже повідомлення та через кілька секунд перенаправить на домен API. Потім бекенд автоматично редиректить на `https://work-e.netlify.app/sign-up?error=user_cancelled_login`.

Фронтенд має обробляти цей параметр `error` у роуті `/sign-up` та відображати відповідне повідомлення.

```js
// Наприклад, у компоненті SignUp
const params = new URLSearchParams(location.search);
const error = params.get('error');
if (error === 'user_cancelled_login') {
  alert('Ви відмінили вхід через LinkedIn. Спробуйте ще раз або увійдіть іншим способом.');
}
```

## 6. Додаткові рекомендації

- **Термін дії токена**: контролюйте час життя та обробляйте помилки авторизації.
- **Безпека**: використовуйте HTTPS на всіх етапах.
- **Тестування**: перевірте як успішний, так і відкладений (cancel) flows.

---

*Автор: Команда Work-E*
