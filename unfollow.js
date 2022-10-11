'use strict';

const INSTAGRAM_HOSTNAME = 'www.instagram.com';

let nonFollowersList = [];
let userIdsToUnfollow = [];
let isActiveProcess = false;

// Prompt user if he tries to leave while in the middle of a process (searching / unfollowing / etc..)
// This is especially good for avoiding accidental tab closing which would result in a frustrating experience.
window.addEventListener('beforeunload', e => {
    if (!isActiveProcess) {
        return;
    }
    e = e || window.event;

    // For IE and Firefox prior to version 4
    if (e) {
        e.returnValue = 'Changes you made may not be saved.';
    }

    // For Safari
    return 'Changes you made may not be saved.';
});

function sleep(ms) {
    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function afterUrlGenerator(nextCode) {
    const ds_user_id = getCookie('ds_user_id');
    return `https://www.instagram.com/graphql/query/?query_hash=3dec7e2c57367ef3da3d987d89f9dbc8&variables={"id":"${ds_user_id}","include_reel":"true","fetch_mutual":"false","first":"24","after":"${nextCode}"}`;
}

function unfollowUserUrlGenerator(idToUnfollow) {
    return `https://www.instagram.com/web/friendships/${idToUnfollow}/unfollow/`;
}

function getElementByClass(className) {
    const el = document.querySelector(className);
    if (el === null) {
        throw new Error(`Unable to find element by class: ${className}`);
    }
    return el;
}

function getUserById(userId) {
    const user = nonFollowersList.find(user => {
        return user.id.toString() === userId.toString();
    });
    if (user === undefined) {
        console.error(`Unable to find user by id. userId: ${userId}`);
    }
    return user;
}

function copyListToClipboard() {
    const sortedList = [...nonFollowersList].sort((a, b) => (a.username > b.username ? 1 : -1));

    let output = '';
    sortedList.forEach(user => {
        output += user.username + '\n';
    });

    copyToClipboard(output);
}

async function copyToClipboard(text) {
    await navigator.clipboard.writeText(text);
    alert('List copied to clipboard!');
}

function onToggleUser() {
    getElementByClass('.iu_selected-count').innerHTML = `[${userIdsToUnfollow.length}]`;
}

// Some functions needed to be placed on the window.
// This is due to the way the are used in the inlined template here.
// Placing them on the window was the only way to make them work for some reason.
window.toggleUser = userId => {
    if (userIdsToUnfollow.indexOf(userId) === -1) {
        userIdsToUnfollow = [...userIdsToUnfollow, userId];
    } else {
        userIdsToUnfollow = userIdsToUnfollow.filter(id => id !== userId);
    }
    onToggleUser();
};

window.toggleAllUsers = (status = false) => {
    document.querySelectorAll('.iu_account-checkbox').forEach(e => (e.checked = status));
    if (!status) {
        userIdsToUnfollow = [];
    } else {
        userIdsToUnfollow = nonFollowersList.map(user => user.id);
    }
    onToggleUser();
};

async function run(shouldIncludeVerifiedAccounts) {
    getElementByClass('.iu_main-btn').remove();
    getElementByClass('.iu_include-verified-checkbox').disabled = true;
    nonFollowersList = await getNonFollowersList(shouldIncludeVerifiedAccounts);
    getElementByClass('.ui_copy-list-btn').disabled = false;
}

async function getNonFollowersList(shouldIncludeVerifiedAccounts = true) {
    if (isActiveProcess) {
        return;
    }

    let list = [];
    let hasNext = true;
    let scrollCycle = 0;
    let currentFollowedUsersCount = 0;
    let totalFollowedUsersCount = -1;
    isActiveProcess = true;

    const ds_user_id = getCookie('ds_user_id');
    let url = `https://www.instagram.com/graphql/query/?query_hash=3dec7e2c57367ef3da3d987d89f9dbc8&variables={"id":"${ds_user_id}","include_reel":"true","fetch_mutual":"false","first":"24"}`;

    getElementByClass('.iu_progressbar-container').style.display = 'block';
    const elProgressbarBar = getElementByClass('.iu_progressbar-bar');
    const elProgressbarText = getElementByClass('.iu_progressbar-text');
    const elNonFollowerCount = getElementByClass('.iu_nonfollower-count');
    const elSleepingContainer = getElementByClass('.iu_sleeping-container');

    while (hasNext) {
        let receivedData;
        try {
            receivedData = await fetch(url).then(res => res.json());
        } catch (e) {
            console.error(e);
            continue;
        }

        if (totalFollowedUsersCount === -1) {
            totalFollowedUsersCount = receivedData.data.user.edge_follow.count;
        }

        hasNext = receivedData.data.user.edge_follow.page_info.has_next_page;
        url = afterUrlGenerator(receivedData.data.user.edge_follow.page_info.end_cursor);
        currentFollowedUsersCount += receivedData.data.user.edge_follow.edges.length;

        receivedData.data.user.edge_follow.edges.forEach(x => {
            if (!shouldIncludeVerifiedAccounts && x.node.is_verified) {
                return;
            }
            if (!x.node.follows_viewer) {
                list.push(x.node);
            }
        });

        const percentage = `${Math.ceil((currentFollowedUsersCount / totalFollowedUsersCount) * 100)}%`;
        elProgressbarText.innerHTML = percentage;
        elProgressbarBar.style.width = percentage;
        elNonFollowerCount.innerHTML = list.length.toString();
        renderResults(list);

        await sleep(Math.floor(Math.random() * (1000 - 600)) + 1000);
        scrollCycle++;
        if (scrollCycle > 6) {
            scrollCycle = 0;
            elSleepingContainer.style.display = 'block';
            elSleepingContainer.innerHTML = 'Sleeping 10 secs to prevent getting temp blocked...';
            await sleep(10000);
        }
        elSleepingContainer.style.display = 'none';
    }
    elProgressbarBar.style.backgroundColor = '#59A942';
    elProgressbarText.innerHTML = 'DONE';

    isActiveProcess = false;
    return list;
}

window.unfollow = async () => {
    if (isActiveProcess) {
        return;
    }
    if (userIdsToUnfollow.length === 0) {
        alert('Must select at least a single user to unfollow');
        return;
    }
    if (!confirm('Are you sure?')) {
        return;
    }

    let csrftoken = getCookie('csrftoken');
    if (csrftoken === undefined) {
        throw new Error('csrftoken cookie is undefined');
    }
    const elSleepingContainer = getElementByClass('.iu_sleeping-container');
    getElementByClass('.iu_toggle-all-checkbox').disabled = true;
    const elResultsContainer = getElementByClass('.iu_results-container');
    elResultsContainer.innerHTML = '';

    const scrollToBottom = () => window.scrollTo(0, elResultsContainer.scrollHeight);

    isActiveProcess = true;
    let counter = 0;
    for (const id of userIdsToUnfollow) {
        const user = getUserById(id);
        try {
            await fetch(unfollowUserUrlGenerator(id), {
                headers: {
                    'content-type': 'application/x-www-form-urlencoded',
                    'x-csrftoken': csrftoken,
                },
                method: 'POST',
                mode: 'cors',
                credentials: 'include',
            });
            elResultsContainer.innerHTML += `<div style='padding:1rem;'>Unfollowed
                <a style='color:inherit' target='_blank' href='${INSTAGRAM_HOSTNAME}/${user.username}/'> ${
                user.username
            }</a>
                <span style='color:#00ffff'> [${counter + 1}/${userIdsToUnfollow.length}]</span>
            </div>`;
        } catch (e) {
            console.error(e);
            elResultsContainer.innerHTML += `<div style='padding:1rem;color:red;'>Failed to unfollow ${
                user.username
            } [${counter + 1}/${userIdsToUnfollow.length}]</div>`;
        }
        scrollToBottom();
        await sleep(Math.floor(Math.random() * (6000 - 4000)) + 4000);

        counter += 1;
        // If unfollowing the last user in the list, no reason to wait 5 minutes.
        if (id === userIdsToUnfollow[userIdsToUnfollow.length - 1]) {
            break;
        }
        if (counter % 5 === 0) {
            elSleepingContainer.style.display = 'block';
            elSleepingContainer.innerHTML = 'Sleeping 5 minutes to prevent getting temp blocked...';
            scrollToBottom();
            await sleep(300000);
        }
        elSleepingContainer.style.display = 'none';
    }

    isActiveProcess = false;
    elResultsContainer.innerHTML += `<hr /><div style='padding:1rem;font-size:1.25em;color:#56d756;'>All DONE!</div><hr />`;
    scrollToBottom();
};

function init() {
    if (location.hostname !== INSTAGRAM_HOSTNAME) {
        alert('Can be used only on Instagram routes');
        return;
    }
    document.title = 'InstagramUnfollowers';
    renderOverlay();
}

init();