document.getElementById('user-question').addEventListener('input', function(event) {
    let userInput = event.target.value;

    if (userInput.trim() === "") {
        document.getElementById('suggestions-container').innerHTML = "";
        return;
    }

    // ارسال درخواست برای دریافت پیشنهادات مشابه
    fetch('http://127.0.0.1:5000/suggestions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ input: userInput })
    })
    .then(response => response.json())
    .then(data => {
        let suggestionsHTML = data.suggestions.map(suggestion => 
            `<div class="suggestion-item" onclick="selectSuggestion('${suggestion}')">${suggestion}</div>`
        ).join('');
        document.getElementById('suggestions-container').innerHTML = suggestionsHTML;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

function selectSuggestion(suggestion) {
    document.getElementById('user-question').value = suggestion;
    document.getElementById('suggestions-container').innerHTML = ""; // پاک کردن پیشنهادات پس از انتخاب
}

document.getElementById('question-form').addEventListener('submit', function(event) {
    event.preventDefault();
    let userQuestion = document.getElementById('user-question').value;

    if (userQuestion.trim() === "") {
        alert("لطفاً سوال خود را وارد کنید.");
        return;
    }

    fetch('http://127.0.0.1:5000/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: userQuestion })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('response-container').innerText = data.answer;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
