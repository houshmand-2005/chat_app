const BaseUrl = "http://127.0.0.1:8000";
const FrontBaseUrl = "http://127.0.0.1";

const username = getCookie("username");
const token = getCookie("token");
if (token && username) {
  console.log(username);
} else window.location.href = FrontBaseUrl + "/login.html";

document.addEventListener("DOMContentLoaded", () => {
  const userGroupsList = document.getElementById("user-groups");

  const headers = new Headers({
    Authorization: `Bearer ${token}`,
  });
  const emojis = [
    "⭐",
    "🎉",
    "🎆",
    "💪",
    "❄️",
    "🎈",
    "❤️",
    "✨",
    "🖼️",
    "💎",
    "📞",
    "☔",
    "🍎",
    "😀",
    "🤣",
    "😎",
    "🤑",
    "😇",
    "🤡",
    "👻",
    "💩",
    "🐒",
    "🐞",
    "🦴",
    "🫅",
    "🥝",
    "🍉",
    "🌵",
    "🚗",
    "🛻",
    "🚚",
    "🚢",
    "🌏",
    "🎸",
    "🗿",
    "⌛",
    "🍕",
    "☘️",
    "🦆",
    "🏦",
    "💃",
  ];

  function addGroupToList(group) {
    const listItem = document.createElement("li");
    listItem.classList.add(
      "list-group-item",
      "d-flex",
      "justify-content-between",
      "align-items-start"
    );
    listItem.id = "list_groups";
    const groupContent = document.createElement("div");
    groupContent.classList.add("ms-2", "me-auto");

    const groupName = document.createElement("div");
    groupName.classList.add("fw-bold");
    if (group.notfound) {
      groupName.style.fontSize = "1rem";
    }
    groupName.textContent = `${group.name}`;
    groupContent.appendChild(groupName);
    if (group.notfound) {
    } else {
      const groupDescription = document.createTextNode("@" + group.address);
      groupContent.appendChild(groupDescription);
    }

    const badge = document.createElement("span");
    badge.classList.add("badge", "bg-secondary", "rounded-pill");
    const randomIndex = Math.floor(Math.random() * emojis.length);
    const randomEmoji = emojis[randomIndex];
    badge.textContent = randomEmoji;

    listItem.appendChild(groupContent);
    listItem.appendChild(badge);

    listItem.addEventListener("click", () => {
      setCookie("group", group.id, 1);
      setCookie("group_name", group.name, 1);
      window.location.href = FrontBaseUrl + "/chat.html";
    });

    userGroupsList.appendChild(listItem);
  }

  // Your existing fetch code to get user groups remains the same
  fetch(BaseUrl + "/user/groups", { headers })
    .then((response) => response.json())
    .then((data) => {
      if (data.groups === undefined || data.groups.length == 0) {
        (noGroup = {
          id: "",
          name: "You aren't a member of any group😴",
          address: "",
          notfound: true,
        }),
          addGroupToList(noGroup);
      }
      data.groups.forEach((group) => {
        addGroupToList(group);
      });
    })
    .catch((error) => console.error("Error:", error));
});

function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
  let expires = "expires=" + d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}
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

function joinGroup(username) {
  const headers = new Headers({
    Authorization: `Bearer ${token}`,
  });
  fetch(BaseUrl + `/group/join?address=${username}`, {
    method: "POST",
    headers: headers,
  })
    .then((response) => {
      if (response.status == "404") {
        alert(
          "This group is not available. Please be careful in entering the username."
        );
      } else response.json();
    })
    .then((data) => {
      console.log(data);
      window.location.reload();
    })
    .catch((error) =>
      alert(
        "This group is not available. Please be careful in entering the username."
      )
    );
}

function createGroup(username, name) {
  console.log(username, name);
  const headers = new Headers({
    Authorization: `Bearer ${token}`,
  });
  fetch(BaseUrl + `/group/create/?address=${username}&name=${name}`, {
    method: "POST",
    headers: headers,
  })
    .then((response) => {
      if (response.status == "400") {
        alert("This username already exists");
      } else response.json();
    })
    .then((data) => {
      console.log(data);
      window.location.reload();
    })
    .catch((error) => alert("There is a problem creating the group"));
}
joinButton.addEventListener("click", function () {
  var username = document.getElementById("username").value;

  joinGroup(username);
});

create_group_btn.addEventListener("click", function () {
  var username = document.getElementById("create_username").value;
  var groupname = document.getElementById("create_groupname").value;

  createGroup(username, groupname);
});
function handleLogoutClick() {
  document.cookie = "username=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  document.cookie = "group=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  document.cookie =
    "group_name=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";

  console.log("User clicked LogOut");
  window.location.href = FrontBaseUrl + "/login.html";
}
const headers = new Headers({
  Authorization: `Bearer ${token}`,
});
fetch(BaseUrl + "/user/me", { headers }).then((response) => {
  if (response.status != "200") {
    handleLogoutClick();
  }
});
