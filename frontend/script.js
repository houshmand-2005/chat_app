const msgerForm = get(".msger-inputarea");
const msgerInput = get(".msger-input");
const msgerChat = get(".msger-chat");

const BaseUrl = "http://127.0.0.1:8000";
const FrontBaseUrl = "http://127.0.0.1";
const WebSocketBaseUrl = "ws://127.0.0.1:8000";

const BOT_IMG = "images/icons8-male-user-96.png";
const PERSON_IMG = "images/icons8-male-user-94.png";
let last_message_id = 0;
token = getCookie("token");
group_id = getCookie("group");
let socketSendMessage;
let socketGetUnreadMessages;
const headers = new Headers({
  Authorization: `Bearer ${token}`,
});
function checkToken() {
  fetch(BaseUrl + "/user/me", { headers }).then((response) => {
    if (response.status != "200") {
      handleLogoutClick();
    }
  });
}
checkToken();
async function connectWebSocket() {
  token = getCookie("token");
  group_id = getCookie("group");

  socketSendMessage = new WebSocket(
    WebSocketBaseUrl + `/send-message?token=${token}&group_id=${group_id}`
  );
  socketSendMessage.onclose = function (event) {
    console.log(`WebSocket Closed with Code ${event.code}`);
    checkToken();
    alert("Your Connection Was Cropped Try To Connect Again");
    setTimeout(connectWebSocket, 6000);
  };

  socketGetUnreadMessages = new WebSocket(
    WebSocketBaseUrl +
      `/get-unread-messages?token=${token}&group_id=${group_id}`
  );
  console.log(socketGetUnreadMessages);
  socketGetUnreadMessages.onopen = function (event) {
    console.log(
      "WebSocket Connection for Receiving Unread Messages Established"
    );
  };

  socketGetUnreadMessages.onmessage = function (event) {
    const messageData = JSON.parse(event.data);
    // console.log(messageData);
    const type = messageData.type;
    // console.log(type);
    if (type == "Edit" || type == "Delete") {
      const messageText = messageData.new_text;
      const id = messageData.id;
      console.log(id);
      // console.log(messageText);
      const element = document.getElementById(id);
      if (type == "Edit") {
        if (element) {
          // Change the text content
          element.textContent = messageText;
          if (document.getElementById("edited-indication")) {
          } else {
            const editIndication = document.createElement("span");
            editIndication.textContent = " (Edited)";
            editIndication.className = "edited-indication";
            editIndication.id = "edited-indication";
            element.parentNode.appendChild(editIndication);
          }
        }
      } else {
        element.textContent = "";
        const editIndication = document.createElement("span");
        editIndication.textContent = "This message has been deleted";
        editIndication.className = "deleted-indication";
        element.parentNode.appendChild(editIndication);
      }
    } else {
      const messageText = messageData.text;
      const senderName = messageData.sender_name;
      const id = messageData.id;
      const datetime = messageData.datetime;
      console.log(id);
      // console.log(messageText);

      if (senderName == getCookie("username")) {
        appendMessage(
          senderName,
          PERSON_IMG,
          "right",
          messageText,
          id,
          datetime
        );
      } else {
        appendMessage(senderName, BOT_IMG, "left", messageText, id, datetime);
      }
    }
  };

  socketGetUnreadMessages.onclose = function (event) {
    console.log(`WebSocket Closed with Code ${event.code}`);
    alert("Your Connection Was Cropped Try To Connect Again");
    setTimeout(connectWebSocket, 6000);
  };
}
msgerForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const msgText = msgerInput.value;
  if (!msgText) return;
  if (socketSendMessage.readyState === WebSocket.OPEN) {
    socketSendMessage.send(msgText);
    msgerInput.value = "";
  }
});

function draw_line(callback) {
  const msgHTML = `
  <center><div
  class="alert alert-info"
  role="alert"
  id="unread"
>
  Unread Messages👇
</div></center>`;

  msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  msgerChat.scrollTop += 500;

  if (typeof callback === "function") {
    callback();
  }
}
function appendMessage(name, img, side, text, id, datetime = null) {
  //   Simple solution for small apps
  // console.log(datetime);
  if (datetime == null) {
    datetime = formatDate(new Date());
  } else {
    var datetimeObject = new Date(datetime + "Z");
    var options = {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    };
    var formattedDatetime = datetimeObject.toLocaleDateString("en-US", options);
    datetime = formattedDatetime;
  }
  // console.log(datetime);
  if (side == "right") {
    edit_delete = `
  <div class="msg-info-time"><img src="images/bin.png" width="14" height="14" border="0" onclick="deleteMessage(${id})"/></div>
  <div class="msg-info-time">&nbsp;</div>
  <div class="msg-info-time"><img src="images/edit.png" width="14" height="14" border="0" onclick="editMessage(${id})"/></div>
  <div class="msg-info-time">&nbsp;&nbsp;</div>`;
  } else {
    edit_delete = `<div class="msg-info-time">&nbsp;&nbsp;</div>`;
  }
  const msgHTML = `
    <div class="msg ${side}-msg">
      <div class="msg-img" style="background-image: url(${img})"></div>

      <div class="msg-bubble">
        <div class="msg-info">
          <div class="msg-info-name">${name}</div>
          ${edit_delete}
          <div class="msg-info-time">${datetime}</div>
        </div>

        <div class="msg-text" id="${id}">${text}</div>
      </div>
    </div>
  `;

  msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  msgerChat.scrollTop += 500;
}

// Utils
function get(selector, root = document) {
  return root.querySelector(selector);
}

function formatDate(date) {
  const h = "0" + date.getHours();
  const m = "0" + date.getMinutes();

  return `${h.slice(-2)}:${m.slice(-2)}`;
}

async function get_unread_message_id() {
  let endpointUrl = BaseUrl + `/message/${group_id}/first-unread-message`;
  try {
    const response = await fetch(endpointUrl, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      first_unread_message = -1;
    } else {
      const data = await response.json();
      first_unread_message = data;
      console.log(`First Unread Message Id ${data}`);
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
    throw error;
  }
}
async function write_old_messages() {
  url = BaseUrl + `/group/${group_id}/messages`;
  try {
    await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((messageData) => {
        if (messageData == null) {
        } else {
          const messages = messageData;
          messages.forEach((message) => {
            // console.log(message);
            let username = message.username;
            let messageText = message.message_text;
            const datetime = message.datetime;
            let id = message.message_id;
            if (username == getCookie("username")) {
              appendMessage(
                username,
                PERSON_IMG,
                "right",
                messageText,
                id,
                datetime
              );
            } else
              appendMessage(
                username,
                BOT_IMG,
                "left",
                messageText,
                id,
                datetime
              );
          });
        }
      })
      .catch((error) => console.error("Failed to get OldMessages", error));
  } catch (error) {
    console.error(error);
  }
}

async function old_messages() {
  try {
    await get_unread_message_id();
    await write_old_messages();
  } catch (error) {
    console.error(`${error.message}`);
  }
  if (first_unread_message != -1) {
    draw_line();
  }
}

async function unread_message() {
  return new Promise((resolve, reject) => {
    try {
      connectWebSocket();
      resolve();
    } catch (error) {
      console.error(`${error.message}`);
      reject(error);
    }
  });
}
async function go_to_unread() {
  return new Promise((resolve, reject) => {
    if (first_unread_message != -1) {
      console.log("go to unread!");
      location.hash = "#unread";
    }
    resolve();
  });
}
async function render() {
  try {
    await old_messages();
    await unread_message();
    setTimeout(go_to_unread, 3510);
  } catch (error) {
    console.error(`${error.message}`);
  }
}

render();

function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == " ") {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

const username = getCookie("username");
if (token && username) {
  console.log("login");
  console.log(username);
} else window.location.href = FrontBaseUrl + "/login.html";
const group_name = getCookie("group_name");
if (group_id && group_name) {
  console.log(group_id);
  console.log(group_name);
} else window.location.href = FrontBaseUrl + "/";

const group_name_text = document.getElementById("group_name_text");
group_name_text.textContent = group_name + " ";

function handleLogoutClick() {
  document.cookie = "username=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  document.cookie = "group=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  document.cookie =
    "group_name=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";

  console.log("User clicked LogOut");
  window.location.href = FrontBaseUrl + "/";
}
const logoutButton = document.getElementById("logout-button");
logoutButton.addEventListener("click", handleLogoutClick);
const show_members = document.getElementById("show_members");
function fetchGroupMembers() {
  const headers = new Headers({
    Authorization: `Bearer ${token}`,
  });
  try {
    fetch(BaseUrl + `/group/${group_id}/members`, { headers })
      .then((response) => response.json())
      .then((data) => {
        data.members.forEach((element) => {
          show_members.textContent += element + " ¦ ";
        });
      })
      .catch((error) => console.error("Failed to fetch group members:", error));
  } catch (error) {
    console.error(error);
  }
}
fetchGroupMembers();

function deleteMessage(id) {
  const headers = new Headers({
    Authorization: `Bearer ${token}`,
  });
  try {
    fetch(BaseUrl + `/message/${id}`, {
      method: "DELETE",
      headers: headers,
    })
      .then((response) => response.json())
      .then((data) => {})
      .catch((error) => console.error("Failed to fetch deleteMessage", error));
  } catch (error) {}
}

function editMessage(id) {
  myPopup.classList.add("show");
  closePopup.addEventListener("click", function () {
    myPopup.classList.remove("show");
  });
  editButton.addEventListener("click", function () {
    txt = document.getElementById("edit_text_fill").value;
    editMessageFun(id, txt);
  });
  const original_text = document.getElementById(id);
  const element = document.getElementById("edit_text_fill");
  element.value = original_text.textContent;

  window.addEventListener("click", function (event) {
    if (event.target == myPopup) {
      myPopup.classList.remove("show");
    }
  });
}
closePopup.addEventListener("click", function () {
  myPopup.classList.remove("show");
});
function editMessageFun(id, new_text) {
  const headers = new Headers({
    Authorization: `Bearer ${token}`,
  });
  fetch(BaseUrl + `/message/${id}?changed_message=${new_text}`, {
    method: "PUT",
    headers: headers,
  })
    .then((response) => response.json())
    .then((data) => {})
    .catch((error) => console.error("Failed to fetch editMessageFun", error));
  myPopup.classList.remove("show");
}
