import assert from "node:assert/strict";
import test from "node:test";

import { getOnboarding, saveOnboarding } from "./onboarding.js";

const values = new Map();
global.localStorage = {
  getItem: (key) => values.get(key) ?? null,
  setItem: (key, value) => values.set(key, value),
};

test("stores onboarding by user and ignores invalid data", () => {
  saveOnboarding("user-1", { focus: "trends" });
  assert.deepEqual(getOnboarding("user-1"), { focus: "trends" });
  localStorage.setItem("carbontrace:onboarding:user-2", "broken");
  assert.equal(getOnboarding("user-2"), null);
});
