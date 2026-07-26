const state = {

    models: [],

    selectedModel: null,

    currentChat: null,

    generating: false,

    selectedQuestionAnswer: null
};


const el = {

    newChat:
        document.getElementById(
            "new-chat"
        ),

    chatList:
        document.getElementById(
            "chat-list"
        ),

    modelButton:
        document.getElementById(
            "model-picker-button"
        ),

    modelMenu:
        document.getElementById(
            "model-menu"
        ),

    modelOptions:
        document.getElementById(
            "model-options"
        ),

    modelName:
        document.getElementById(
            "selected-model-name"
        ),

    modelMode:
        document.getElementById(
            "selected-model-mode"
        ),

    modelFooter:
        document.getElementById(
            "active-model-footer"
        ),

    welcome:
        document.getElementById(
            "welcome-screen"
        ),

    messages:
        document.getElementById(
            "messages"
        ),

    chatArea:
        document.getElementById(
            "chat-area"
        ),

    input:
        document.getElementById(
            "message-input"
        ),

    send:
        document.getElementById(
            "send-button"
        ),

    apiButton:
        document.getElementById(
            "api-keys-button"
        ),

    apiModal:
        document.getElementById(
            "api-modal"
        ),

    apiKeyName:
        document.getElementById(
            "api-key-name"
        ),

    createApiKey:
        document.getElementById(
            "create-api-key"
        ),

    apiKeyList:
        document.getElementById(
            "api-key-list"
        ),

    newKeyBox:
        document.getElementById(
            "new-key-box"
        ),

    newApiKey:
        document.getElementById(
            "new-api-key"
        ),

    copyApiKey:
        document.getElementById(
            "copy-api-key"
        ),

    logout:
        document.getElementById(
            "logout-button"
        ),

    toast:
        document.getElementById(
            "toast-container"
        ),

    questionModal:
        document.getElementById(
            "question-modal"
        ),

    questionTitle:
        document.getElementById(
            "question-title"
        ),

    questionText:
        document.getElementById(
            "question-text"
        ),

    questionOptions:
        document.getElementById(
            "question-options"
        ),

    questionAnswer:
        document.getElementById(
            "question-custom-answer"
        ),

    questionSubmit:
        document.getElementById(
            "question-submit"
        ),

    questionCancel:
        document.getElementById(
            "question-cancel"
        )
};


document.addEventListener(
    "DOMContentLoaded",
    initialize
);


async function initialize() {

    configureMarkdown();

    setupEvents();

    await loadModels();

    await loadChats();

    await checkStatus();

    resizeInput();

    updateSendButton();

    el.input.focus();
}


// ============================================================
// MARKDOWN
// ============================================================

function configureMarkdown() {

    if (
        typeof marked ===
        "undefined"
    ) {

        return;
    }


    marked.setOptions({

        gfm: true,

        breaks: true
    });
}


function renderMarkdown(text) {

    if (
        typeof marked ===
        "undefined"
    ) {

        return escapeHTML(
            text
        ).replace(
            /\n/g,
            "<br>"
        );
    }


    let html =
        marked.parse(
            text || ""
        );


    if (
        typeof DOMPurify !==
        "undefined"
    ) {

        html =
            DOMPurify.sanitize(
                html
            );
    }


    return html;
}


// ============================================================
// MODELS
// ============================================================

async function loadModels() {

    const response =
        await fetch(
            "/api/models"
        );


    if (
        response.status === 401
    ) {

        location.href =
            "/login";

        return;
    }


    const data =
        await response.json();


    state.models =
        data.models || [];


    renderModels();


    const saved =
        localStorage.getItem(
            "localgpt-model"
        );


    state.selectedModel =

        state.models.find(
            model =>
                model.id === saved
                &&
                model.available
        )

        ||

        state.models.find(
            model =>
                model.id ===
                    data.default
                &&
                model.available
        )

        ||

        state.models.find(
            model =>
                model.available
        );


    if (
        state.selectedModel
    ) {

        updateModelUI(
            state.selectedModel
        );
    }
}


function renderModels() {

    el.modelOptions.innerHTML =
        "";


    state.models.forEach(
        model => {

            const button =
                document.createElement(
                    "button"
                );


            button.className =
                "model-option";


            button.dataset.model =
                model.id;


            button.innerHTML = `

                <div class="model-icon">
                    <i class="fa-solid fa-sparkles"></i>
                </div>

                <div class="model-option-info">

                    <span class="model-option-name">
                        ${escapeHTML(model.name)}
                    </span>

                    <span class="model-option-description">
                        ${escapeHTML(model.description)}
                        ${model.available ? "" : " • Missing"}
                    </span>

                </div>

                <i class="fa-solid fa-check model-check"></i>
            `;


            if (!model.available) {

                button.disabled =
                    true;

                button.style.opacity =
                    ".4";
            }


            button.addEventListener(
                "click",
                () =>
                    switchModel(
                        model
                    )
            );


            el.modelOptions
                .appendChild(
                    button
                );
        }
    );
}


async function switchModel(
    model
) {

    if (
        state.generating
        ||
        !model.available
    ) {

        return;
    }


    el.modelMenu.classList.add(
        "hidden"
    );


    if (
        state.selectedModel?.id
        === model.id
    ) {

        return;
    }


    const previous =
        state.selectedModel;


    el.modelName.textContent =
        `Loading ${model.name}...`;


    el.modelMode.textContent =
        "Please wait";


    showToast(
        `Loading ${model.name}`
    );


    try {

        const response =
            await fetch(
                "/api/models/switch",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            model:
                                model.id
                        })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error
            );
        }


        state.selectedModel =
            model;


        localStorage.setItem(
            "localgpt-model",
            model.id
        );


        updateModelUI(
            model
        );


        showToast(
            `${model.name} ready`
        );

    }

    catch (error) {

        if (previous) {

            state.selectedModel =
                previous;

            updateModelUI(
                previous
            );
        }


        showToast(
            error.message
        );
    }
}


function updateModelUI(
    model
) {

    el.modelName.textContent =
        model.name;


    el.modelMode.textContent =
        model.description;


    el.modelFooter.textContent =
        model.name;


    document
        .querySelectorAll(
            ".model-option"
        )
        .forEach(
            option => {

                option.classList
                    .remove(
                        "active"
                    );


                const check =
                    option.querySelector(
                        ".model-check"
                    );


                if (check) {

                    check.style
                        .visibility =
                        "hidden";
                }
            }
        );


    const selected =
        document.querySelector(
            `[data-model="${model.id}"]`
        );


    if (selected) {

        selected.classList.add(
            "active"
        );


        const check =
            selected.querySelector(
                ".model-check"
            );


        if (check) {

            check.style.visibility =
                "visible";
        }
    }
}


// ============================================================
// CHATS
// ============================================================

async function loadChats() {

    const response =
        await fetch(
            "/api/chats"
        );


    const chats =
        await response.json();


    renderChats(
        chats
    );
}


function renderChats(
    chats
) {

    el.chatList.innerHTML =
        "";


    if (!chats.length) {

        const empty =
            document.createElement(
                "div"
            );


        empty.style.cssText =
            "color:#777;font-size:12px;padding:10px;";


        empty.textContent =
            "No conversations yet";


        el.chatList.appendChild(
            empty
        );


        return;
    }


    chats.forEach(
        chat => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "chat-item";


            if (
                Number(
                    state.currentChat
                )
                ===
                Number(
                    chat.id
                )
            ) {

                item.classList.add(
                    "active"
                );
            }


            const title =
                document.createElement(
                    "div"
                );


            title.className =
                "chat-title";


            title.textContent =
                chat.title;


            title.onclick =
                () =>
                    openChat(
                        chat.id
                    );


            const menu =
                document.createElement(
                    "button"
                );


            menu.className =
                "chat-menu-button";


            menu.innerHTML =
                '<i class="fa-solid fa-ellipsis"></i>';


            menu.onclick =
                event => {

                    event.stopPropagation();

                    chatMenu(
                        chat
                    );
                };


            item.append(
                title,
                menu
            );


            el.chatList
                .appendChild(
                    item
                );
        }
    );
}


async function openChat(
    chatId
) {

    if (
        state.generating
    ) {

        return;
    }


    const response =
        await fetch(
            `/api/chats/${chatId}`
        );


    const chat =
        await response.json();


    if (!response.ok) {

        showToast(
            chat.error
        );

        return;
    }


    state.currentChat =
        chat.id;


    const model =
        state.models.find(
            model =>
                model.id ===
                chat.model
        );


    if (
        model
        &&
        model.available
    ) {

        state.selectedModel =
            model;

        updateModelUI(
            model
        );
    }


    el.messages.innerHTML =
        "";


    showConversation();


    chat.messages.forEach(
        message => {

            if (
                message.role ===
                "user"
            ) {

                addUserMessage(
                    message.content,
                    false
                );

            }

            else if (
                message.role ===
                "assistant"
            ) {

                addAssistantMessage(
                    message.content,
                    message.model,
                    false
                );
            }
        }
    );


    await loadChats();

    scrollBottom();
}


function newChat() {

    if (
        state.generating
    ) {

        return;
    }


    state.currentChat =
        null;


    el.messages.innerHTML =
        "";


    el.welcome.classList
        .remove(
            "hidden"
        );


    el.input.value =
        "";


    resizeInput();

    updateSendButton();

    loadChats();

    el.input.focus();
}


function chatMenu(
    chat
) {

    const action =
        prompt(
            `Type:\n\nrename - Rename chat\ndelete - Delete chat`,
            ""
        );


    if (!action) {

        return;
    }


    if (
        action.toLowerCase()
        === "rename"
    ) {

        renameChat(
            chat
        );
    }


    if (
        action.toLowerCase()
        === "delete"
    ) {

        deleteChat(
            chat.id
        );
    }
}


async function renameChat(
    chat
) {

    const title =
        prompt(
            "New chat title:",
            chat.title
        );


    if (!title?.trim()) {

        return;
    }


    await fetch(
        `/api/chats/${chat.id}`,
        {

            method: "PATCH",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify({
                    title:
                        title.trim()
                })
        }
    );


    await loadChats();
}


async function deleteChat(
    chatId
) {

    if (
        !confirm(
            "Delete this conversation?"
        )
    ) {

        return;
    }


    await fetch(
        `/api/chats/${chatId}`,
        {
            method: "DELETE"
        }
    );


    if (
        Number(
            state.currentChat
        )
        ===
        Number(
            chatId
        )
    ) {

        newChat();
    }


    await loadChats();
}


// ============================================================
// MESSAGES
// ============================================================

function showConversation() {

    el.welcome.classList.add(
        "hidden"
    );
}


function addUserMessage(
    content,
    scroll = true
) {

    showConversation();


    const wrapper =
        document.createElement(
            "div"
        );


    wrapper.className =
        "message message-user";


    const bubble =
        document.createElement(
            "div"
        );


    bubble.className =
        "user-bubble";


    bubble.textContent =
        content;


    wrapper.appendChild(
        bubble
    );


    el.messages.appendChild(
        wrapper
    );


    if (scroll) {

        scrollBottom();
    }
}


function addLoading() {

    removeLoading();


    const wrapper =
        document.createElement(
            "div"
        );


    wrapper.className =
        "message";


    wrapper.id =
        "assistant-loading";


    wrapper.innerHTML = `

        <div class="assistant-header">

            <div class="assistant-avatar">
                <i class="fa-solid fa-sparkles"></i>
            </div>

            <span class="assistant-model">
                ${escapeHTML(
                    state.selectedModel?.name
                    || "LocalGPT"
                )}
            </span>

        </div>

        <div class="typing-indicator">

            <span></span>
            <span></span>
            <span></span>

        </div>
    `;


    el.messages.appendChild(
        wrapper
    );


    scrollBottom();
}


function removeLoading() {

    document
        .getElementById(
            "assistant-loading"
        )
        ?.remove();
}


function addAssistantMessage(
    content,
    modelId = null,
    scroll = true
) {

    removeLoading();

    showConversation();


    const model =
        state.models.find(
            model =>
                model.id ===
                modelId
        );


    const name =
        model?.name
        ||
        state.selectedModel?.name
        ||
        "LocalGPT";


    const wrapper =
        document.createElement(
            "div"
        );


    wrapper.className =
        "message";


    const header =
        document.createElement(
            "div"
        );


    header.className =
        "assistant-header";


    header.innerHTML = `

        <div class="assistant-avatar">
            <i class="fa-solid fa-sparkles"></i>
        </div>

        <span class="assistant-model">
            ${escapeHTML(name)}
        </span>
    `;


    const body =
        document.createElement(
            "div"
        );


    body.className =
        "assistant-message";


    body.innerHTML =
        renderMarkdown(
            content
        );


    wrapper.append(
        header,
        body
    );


    const actions =
        document.createElement(
            "div"
        );


    actions.className =
        "message-actions";


    const copy =
        document.createElement(
            "button"
        );


    copy.className =
        "message-action";


    copy.innerHTML =
        '<i class="fa-regular fa-copy"></i>';


    copy.onclick =
        async () => {

            await navigator
                .clipboard
                .writeText(
                    content
                );


            showToast(
                "Response copied"
            );
        };


    actions.appendChild(
        copy
    );


    wrapper.appendChild(
        actions
    );


    el.messages.appendChild(
        wrapper
    );


    enhanceCodeBlocks(
        body
    );


    detectInteractiveQuestion(
        content
    );


    if (scroll) {

        scrollBottom();
    }
}


// ============================================================
// CODE BLOCKS
// ============================================================

const languageExtensions = {

    python: "py",
    py: "py",

    javascript: "js",
    js: "js",

    typescript: "ts",
    ts: "ts",

    java: "java",

    c: "c",

    cpp: "cpp",
    "c++": "cpp",

    csharp: "cs",
    cs: "cs",

    html: "html",

    css: "css",

    json: "json",

    bash: "sh",
    shell: "sh",
    sh: "sh",

    powershell: "ps1",

    sql: "sql",

    xml: "xml",

    yaml: "yaml",
    yml: "yml",

    markdown: "md",
    md: "md",

    text: "txt"
};


function enhanceCodeBlocks(
    container
) {

    const blocks =
        container.querySelectorAll(
            "pre > code"
        );


    blocks.forEach(
        code => {

            const pre =
                code.parentElement;


            if (
                pre.parentElement
                ?.classList
                .contains(
                    "code-block"
                )
            ) {

                return;
            }


            let language =
                "text";


            const className =
                Array
                .from(
                    code.classList
                )
                .find(
                    name =>
                        name.startsWith(
                            "language-"
                        )
                );


            if (className) {

                language =
                    className.replace(
                        "language-",
                        ""
                    );
            }


            if (
                typeof hljs !==
                "undefined"
            ) {

                try {

                    hljs.highlightElement(
                        code
                    );

                }

                catch {
                    // Ignore highlighting failures.
                }
            }


            const shell =
                document.createElement(
                    "div"
                );


            shell.className =
                "code-block";


            const header =
                document.createElement(
                    "div"
                );


            header.className =
                "code-header";


            header.innerHTML = `

                <span class="code-language">
                    ${escapeHTML(language)}
                </span>

                <button class="code-button copy-code">
                    <i class="fa-regular fa-copy"></i>
                    Copy
                </button>

                <button class="code-button save-code">
                    <i class="fa-regular fa-floppy-disk"></i>
                    Save
                </button>
            `;


            pre.parentNode.insertBefore(
                shell,
                pre
            );


            shell.append(
                header,
                pre
            );


            header
                .querySelector(
                    ".copy-code"
                )
                .onclick =
                    async () => {

                        await navigator
                            .clipboard
                            .writeText(
                                code.textContent
                            );


                        showToast(
                            "Code copied"
                        );
                    };


            header
                .querySelector(
                    ".save-code"
                )
                .onclick =
                    () =>
                        saveCode(
                            code.textContent,
                            language
                        );
        }
    );
}


function saveCode(
    content,
    language
) {

    const extension =
        languageExtensions[
            language.toLowerCase()
        ]
        ||
        "txt";


    const suggested =
        `localgpt-code.${extension}`;


    const filename =
        prompt(
            "Save file as:",
            suggested
        );


    if (!filename) {

        return;
    }


    const blob =
        new Blob(
            [content],
            {
                type:
                    "text/plain;charset=utf-8"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const anchor =
        document.createElement(
            "a"
        );


    anchor.href =
        url;


    anchor.download =
        filename;


    document.body.appendChild(
        anchor
    );


    anchor.click();

    anchor.remove();


    URL.revokeObjectURL(
        url
    );


    showToast(
        "Code saved"
    );
}


// ============================================================
// INTERACTIVE QUESTIONS
// ============================================================

/*

Gemma can deliberately emit:

<localgpt-question>
{
    "title": "Choose a framework",
    "question": "Which frontend framework should I use?",
    "options": ["React", "Vue", "Angular"]
}
</localgpt-question>

The UI detects it and displays the modal.

*/

function detectInteractiveQuestion(
    content
) {

    const match =
        content.match(
            /<localgpt-question>([\s\S]*?)<\/localgpt-question>/i
        );


    if (!match) {

        return;
    }


    try {

        const question =
            JSON.parse(
                match[1].trim()
            );


        openQuestionModal(
            question
        );

    }

    catch (error) {

        console.warn(
            "Invalid LocalGPT question:",
            error
        );
    }
}


function openQuestionModal(
    question
) {

    state.selectedQuestionAnswer =
        null;


    el.questionTitle.textContent =
        question.title
        ||
        "LocalGPT has a question";


    el.questionText.textContent =
        question.question
        ||
        "";


    el.questionOptions.innerHTML =
        "";


    el.questionAnswer.value =
        "";


    (
        question.options
        ||
        []
    ).forEach(
        option => {

            const button =
                document.createElement(
                    "button"
                );


            button.className =
                "question-option";


            button.textContent =
                option;


            button.onclick =
                () => {

                    document
                        .querySelectorAll(
                            ".question-option"
                        )
                        .forEach(
                            item =>
                                item.classList
                                    .remove(
                                        "selected"
                                    )
                        );


                    button.classList.add(
                        "selected"
                    );


                    state
                        .selectedQuestionAnswer =
                        option;
                };


            el.questionOptions
                .appendChild(
                    button
                );
        }
    );


    el.questionModal.classList
        .remove(
            "hidden"
        );
}


// ============================================================
// SEND MESSAGE
// ============================================================

async function sendMessage(
    overrideText = null
) {

    const content =
        (
            overrideText
            ??
            el.input.value
        ).trim();


    if (
        !content
        ||
        state.generating
        ||
        !state.selectedModel
    ) {

        return;
    }


    state.generating =
        true;


    if (
        overrideText === null
    ) {

        el.input.value =
            "";
    }


    resizeInput();

    updateSendButton();


    addUserMessage(
        content
    );


    addLoading();


    try {

        const response =
            await fetch(
                "/api/chat",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            message:
                                content,

                            model:
                                state
                                .selectedModel
                                .id,

                            chat_id:
                                state
                                .currentChat
                        })
                }
            );


        const data =
            await response.json();


        if (
            data.chat_id
        ) {

            state.currentChat =
                data.chat_id;
        }


        if (!response.ok) {

            throw new Error(
                data.error
                ||
                "Generation failed."
            );
        }


        addAssistantMessage(
            data.response,
            data.model
        );


        await loadChats();

    }

    catch (error) {

        removeLoading();


        addAssistantMessage(
            `**Error:** ${error.message}`
        );
    }


    finally {

        state.generating =
            false;


        updateSendButton();

        el.input.focus();
    }
}


// ============================================================
// API KEYS
// ============================================================

async function openApiKeys() {

    el.apiModal.classList
        .remove(
            "hidden"
        );


    el.newKeyBox.classList
        .add(
            "hidden"
        );


    await loadApiKeys();
}


async function loadApiKeys() {

    const response =
        await fetch(
            "/api/keys"
        );


    const keys =
        await response.json();


    el.apiKeyList.innerHTML =
        "";


    if (!keys.length) {

        el.apiKeyList.innerHTML =
            '<div style="color:#777;font-size:12px;padding:15px 0">No API keys yet.</div>';

        return;
    }


    keys.forEach(
        key => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "api-key-item";


            row.innerHTML = `

                <div class="api-key-info">

                    <strong>
                        ${escapeHTML(key.name)}
                    </strong>

                    <span>
                        ${escapeHTML(key.prefix)}
                        ${key.revoked ? " • Revoked" : ""}
                    </span>

                </div>

                ${
                    key.revoked
                    ?
                    ""
                    :
                    `
                    <button
                        class="revoke-key"
                    >
                        Revoke
                    </button>
                    `
                }
            `;


            const revoke =
                row.querySelector(
                    ".revoke-key"
                );


            if (revoke) {

                revoke.onclick =
                    async () => {

                        if (
                            !confirm(
                                "Revoke this API key?"
                            )
                        ) {

                            return;
                        }


                        await fetch(
                            `/api/keys/${key.id}`,
                            {
                                method:
                                    "DELETE"
                            }
                        );


                        await loadApiKeys();
                    };
            }


            el.apiKeyList
                .appendChild(
                    row
                );
        }
    );
}


async function createApiKey() {

    const name =
        el.apiKeyName
        .value
        .trim();


    if (!name) {

        showToast(
            "Enter a key name"
        );

        return;
    }


    const response =
        await fetch(
            "/api/keys",
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify({
                        name
                    })
            }
        );


    const data =
        await response.json();


    if (!response.ok) {

        showToast(
            data.error
        );

        return;
    }


    el.newApiKey.textContent =
        data.key;


    el.newKeyBox.classList
        .remove(
            "hidden"
        );


    el.apiKeyName.value =
        "";


    await loadApiKeys();
}


// ============================================================
// STATUS
// ============================================================

async function checkStatus() {

    try {

        const response =
            await fetch(
                "/api/status"
            );


        if (!response.ok) {

            return;
        }


        const data =
            await response.json();


        const status =
            document.querySelector(
                ".local-status"
            );


        if (data.ready) {

            status.innerHTML = `

                <span class="status-dot"></span>

                Local
            `;

        }

        else {

            status.textContent =
                data.status
                ||
                "Loading";
        }

    }

    catch {
        // App unavailable.
    }
}


// ============================================================
// EVENTS
// ============================================================

function setupEvents() {

    el.newChat.onclick =
        newChat;


    el.modelButton.onclick =
        event => {

            event.stopPropagation();

            el.modelMenu.classList
                .toggle(
                    "hidden"
                );
        };


    document.addEventListener(
        "click",
        event => {

            if (
                !el.modelMenu
                    .contains(
                        event.target
                    )
                &&
                !el.modelButton
                    .contains(
                        event.target
                    )
            ) {

                el.modelMenu.classList
                    .add(
                        "hidden"
                    );
            }
        }
    );


    el.input.addEventListener(
        "input",
        () => {

            resizeInput();

            updateSendButton();
        }
    );


    el.input.addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                    "Enter"
                &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendMessage();
            }
        }
    );


    el.send.onclick =
        () =>
            sendMessage();


    document
        .querySelectorAll(
            ".suggestion"
        )
        .forEach(
            button => {

                button.onclick =
                    () => {

                        el.input.value =
                            button.dataset
                            .prompt;


                        resizeInput();

                        updateSendButton();

                        el.input.focus();
                    };
            }
        );


    document.addEventListener(
        "keydown",
        event => {

            if (
                event.ctrlKey
                &&
                event.key
                    .toLowerCase()
                    === "k"
            ) {

                event.preventDefault();

                newChat();
            }
        }
    );


    el.apiButton.onclick =
        openApiKeys;


    el.createApiKey.onclick =
        createApiKey;


    el.copyApiKey.onclick =
        async () => {

            await navigator
                .clipboard
                .writeText(
                    el.newApiKey
                    .textContent
                );


            showToast(
                "API key copied"
            );
        };


    document
        .querySelectorAll(
            "[data-close-modal]"
        )
        .forEach(
            button => {

                button.onclick =
                    () => {

                        document
                            .getElementById(
                                button.dataset
                                    .closeModal
                            )
                            .classList
                            .add(
                                "hidden"
                            );
                    };
            }
        );


    el.logout.onclick =
        async () => {

            await fetch(
                "/api/auth/logout",
                {
                    method:
                        "POST"
                }
            );


            location.href =
                "/login";
        };


    el.questionCancel.onclick =
        () => {

            el.questionModal
                .classList
                .add(
                    "hidden"
                );
        };


    el.questionSubmit.onclick =
        async () => {

            const answer =
                el.questionAnswer
                    .value
                    .trim()
                ||
                state
                    .selectedQuestionAnswer;


            if (!answer) {

                showToast(
                    "Choose or enter an answer"
                );

                return;
            }


            el.questionModal
                .classList
                .add(
                    "hidden"
                );


            await sendMessage(
                answer
            );
        };
}


// ============================================================
// UTILITIES
// ============================================================

function resizeInput() {

    el.input.style.height =
        "auto";


    el.input.style.height =
        Math.min(
            el.input.scrollHeight,
            200
        )
        + "px";
}


function updateSendButton() {

    el.send.disabled =
        (
            !el.input.value.trim()
            ||
            state.generating
            ||
            !state.selectedModel
        );
}


function scrollBottom() {

    requestAnimationFrame(
        () => {

            el.chatArea.scrollTop =
                el.chatArea
                    .scrollHeight;
        }
    );
}


function showToast(
    message
) {

    const toast =
        document.createElement(
            "div"
        );


    toast.className =
        "toast";


    toast.textContent =
        message;


    el.toast.appendChild(
        toast
    );


    setTimeout(
        () =>
            toast.remove(),
        2800
    );
}


function escapeHTML(
    value
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        value ?? "";


    return div.innerHTML;
}


setInterval(
    checkStatus,
    10000
);