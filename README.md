## Запуск проекта

```bash
make build up
```

#### Посмотреть другие команды make

```bash
make help
```

## Как работаем с репой

### 0. Получили задачу в YouGile и берем ее slug
<img width="561" height="328" alt="image" src="https://github.com/user-attachments/assets/30fd75d6-0c2a-4488-a8f8-dc389f6dee49" />

### 1. Прежде чем делать задачу, переключаемся на main и обновляем состояние проекта

```bash
git checkout main
```

```bash
git pull origin main
```

### 2. Cоздаем git-ветку с названием в виде слага

```bash
git checkout -b PRO-8
```

### 3. Делаем задачу, коммитим в созданную ветку. Название коммитов начинаем со слага

```bash
git commit -m 'PRO-8: добавил фичу'
```

### 4. Закончили делать задачу и убедились, что все работает - пушим ветку

```bash
git push --set-upstream origin PRO-8
```

### 5. Делаем ПР из этой ветки в main. В YouGile переводим задачу в "Тестируются"
### 6. Просим коллег поревьюить и потестить выполненную задачу
