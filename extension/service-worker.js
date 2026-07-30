import { collapseVerticalTabs, toggleVerticalTabs } from "./native-host.js";

const startupCollapseDelays = [0, 1000, 3000];
let commandQueue = Promise.resolve();
let startupCollapseTimers = [];

chrome.commands.onCommand.addListener(async (command) => {
  if (command !== "toggle-vertical-tabs") {
    return;
  }

  cancelStartupCollapse();
  await enqueueCommand(toggleVerticalTabSidebar);
});

chrome.action.onClicked.addListener(() => {
  cancelStartupCollapse();
  void enqueueCommand(toggleVerticalTabSidebar);
});

chrome.runtime.onStartup.addListener(scheduleStartupCollapse);

function enqueueCommand(command) {
  const result = commandQueue.then(command);
  commandQueue = result.catch(() => {});
  return result;
}

function scheduleStartupCollapse() {
  startupCollapseTimers = startupCollapseDelays.map((delay, index) =>
    setTimeout(() => {
      void enqueueCommand(() =>
        collapseVerticalTabSidebar(index === startupCollapseDelays.length - 1),
      );
    }, delay),
  );
}

function cancelStartupCollapse() {
  startupCollapseTimers.forEach(clearTimeout);
  startupCollapseTimers = [];
}

async function toggleVerticalTabSidebar() {
  try {
    await toggleVerticalTabs();
  } catch (error) {
    console.error("Could not invoke the native host.", error);
  }
}

async function collapseVerticalTabSidebar(reportFailure) {
  try {
    await collapseVerticalTabs();
  } catch (error) {
    if (reportFailure) {
      console.error(
        "Could not collapse the vertical tab sidebar on startup.",
        error,
      );
    }
  }
}
