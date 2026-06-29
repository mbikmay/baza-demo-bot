const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const months = [
  "Январь",
  "Февраль",
  "Март",
  "Апрель",
  "Май",
  "Июнь",
  "Июль",
  "Август",
  "Сентябрь",
  "Октябрь",
  "Ноябрь",
  "Декабрь",
];

const busyRanges = [
  ["2026-07-05", "2026-07-08"],
  ["2026-07-14", "2026-07-16"],
  ["2026-08-01", "2026-08-04"],
];

const countries = {
  kz: {
    name: "Казахстан",
    city: "Алматы",
    currency: "₸",
    prices: { house_2: 25000, house_4: 35000, house_6: 50000 },
  },
  ru: {
    name: "Россия",
    city: "Москва",
    currency: "₽",
    prices: { house_2: 5000, house_4: 7000, house_6: 10000 },
  },
};

const params = new URLSearchParams(window.location.search);
const countryCode = countries[params.get("country")] ? params.get("country") : "kz";
const country = countries[countryCode];

const houses = [
  {
    code: "house_2",
    title: "Домик Comfort",
    capacity: 2,
    price: country.prices.house_2,
    image: "./photos_optimized/house_2.jpg",
    description: "Для пары: санузел, мини-холодильник, посуда и мангал рядом.",
  },
  {
    code: "house_4",
    title: "Домик Family",
    capacity: 4,
    price: country.prices.house_4,
    image: "./photos_optimized/house_4.jpg",
    description: "Для семьи: две спальни, кухня, душ, терраса и отдельный мангал.",
  },
  {
    code: "house_6",
    title: "Домик Grand",
    capacity: 6,
    price: country.prices.house_6,
    image: "./photos_optimized/house_6.jpg",
    description: "Для компании: гостиная, кухня, несколько спальных мест и зона отдыха.",
  },
];

const state = {
  visible: new Date(),
  checkIn: null,
  checkOut: null,
  house: null,
};

const monthTitle = document.querySelector("#monthTitle");
const days = document.querySelector("#days");
const checkInEl = document.querySelector("#checkIn");
const checkOutEl = document.querySelector("#checkOut");
const nightsEl = document.querySelector("#nights");
const sendButton = document.querySelector("#send");
const housesStep = document.querySelector("#housesStep");
const housesEl = document.querySelector("#houses");
const totalStep = document.querySelector("#totalStep");
const totalPriceEl = document.querySelector("#totalPrice");
const selectedHouseText = document.querySelector("#selectedHouseText");
const countryLabel = document.querySelector("#countryLabel");
const startPrice = document.querySelector("#startPrice");

function toIso(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function fromIso(value) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function formatRu(date) {
  if (!date) return "Не выбран";
  return date.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function money(value) {
  return `${value.toLocaleString("ru-RU")} ${country.currency}`;
}

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function isBusy(date) {
  const time = startOfDay(date).getTime();
  return busyRanges.some(([start, end]) => {
    const startTime = fromIso(start).getTime();
    const endTime = fromIso(end).getTime();
    return time >= startTime && time < endTime;
  });
}

function rangeHasBusy(checkIn, checkOut) {
  const cursor = new Date(checkIn);
  while (cursor < checkOut) {
    if (isBusy(cursor)) return true;
    cursor.setDate(cursor.getDate() + 1);
  }
  return false;
}

function isSameDate(a, b) {
  return a && b && toIso(a) === toIso(b);
}

function isInRange(date) {
  return state.checkIn && state.checkOut && date > state.checkIn && date < state.checkOut;
}

function updateSummary() {
  checkInEl.textContent = formatRu(state.checkIn);
  checkOutEl.textContent = formatRu(state.checkOut);

  const nights = state.checkIn && state.checkOut
    ? Math.max(Math.round((state.checkOut - state.checkIn) / 86400000), 1)
    : 0;

  nightsEl.textContent = String(nights);
  housesStep.classList.toggle("hidden", !(state.checkIn && state.checkOut));
  totalStep.classList.toggle("hidden", !(state.checkIn && state.checkOut && state.house));
  sendButton.classList.toggle("hidden", !(state.checkIn && state.checkOut && state.house));

  if (state.house) {
    totalPriceEl.textContent = money(state.house.price * nights);
    selectedHouseText.textContent = `${state.house.title}, до ${state.house.capacity} гостей`;
  }

  sendButton.disabled = !(state.checkIn && state.checkOut && state.house);
}

function selectDate(date) {
  if (!state.checkIn || state.checkOut || date <= state.checkIn) {
    state.checkIn = date;
    state.checkOut = null;
  } else if (rangeHasBusy(state.checkIn, date)) {
    alert("В выбранном периоде есть занятые даты. Выберите другой выезд.");
  } else {
    state.checkOut = date;
    setTimeout(() => {
      housesStep.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 120);
  }

  updateSummary();
  render();
}

function renderHouses() {
  housesEl.innerHTML = "";

  houses.forEach((house) => {
    const button = document.createElement("button");
    button.className = "house-card";
    button.type = "button";
    if (state.house?.code === house.code) button.classList.add("selected");

    button.innerHTML = `
      <img src="${house.image}" alt="${house.title}" loading="lazy" onerror="this.closest('.house-card').classList.add('no-image'); this.remove();" />
      <div class="house-info">
        <strong>${house.title}</strong>
        <span>До ${house.capacity} гостей · ${money(house.price)} / сутки</span>
        <p>${house.description}</p>
      </div>
    `;

    button.addEventListener("click", () => {
      state.house = house;
      updateSummary();
      renderHouses();
      totalStep.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });

    housesEl.appendChild(button);
  });
}

function render() {
  const year = state.visible.getFullYear();
  const month = state.visible.getMonth();
  const today = startOfDay(new Date());
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const firstWeekday = (first.getDay() + 6) % 7;

  monthTitle.textContent = `${months[month]} ${year}`;
  days.innerHTML = "";

  for (let i = 0; i < firstWeekday; i += 1) {
    const empty = document.createElement("button");
    empty.className = "day empty";
    empty.type = "button";
    days.appendChild(empty);
  }

  for (let day = 1; day <= last.getDate(); day += 1) {
    const date = new Date(year, month, day);
    const button = document.createElement("button");
    button.className = "day";
    button.type = "button";
    button.textContent = String(day);

    if (date < today) button.classList.add("past");
    if (isSameDate(date, today)) button.classList.add("today");
    if (isBusy(date)) button.classList.add("busy");
    if (isSameDate(date, state.checkIn) || isSameDate(date, state.checkOut)) button.classList.add("selected");
    if (isInRange(date)) button.classList.add("in-range");

    button.disabled = date < today || isBusy(date);
    button.addEventListener("click", () => selectDate(date));
    days.appendChild(button);
  }
}

document.querySelector("#prev").addEventListener("click", () => {
  state.visible = new Date(state.visible.getFullYear(), state.visible.getMonth() - 1, 1);
  render();
});

document.querySelector("#next").addEventListener("click", () => {
  state.visible = new Date(state.visible.getFullYear(), state.visible.getMonth() + 1, 1);
  render();
});

document.querySelector("#reset").addEventListener("click", () => {
  state.checkIn = null;
  state.checkOut = null;
  state.house = null;
  updateSummary();
  render();
  renderHouses();
});

sendButton.addEventListener("click", () => {
  if (!(state.checkIn && state.checkOut && state.house)) {
    alert("Сначала выберите даты и домик.");
    return;
  }

  const payload = {
    check_in: toIso(state.checkIn),
    check_out: toIso(state.checkOut),
    nights: Number(nightsEl.textContent),
    country: countryCode,
    house_code: state.house.code,
    house_title: state.house.title,
    house_capacity: state.house.capacity,
    price_per_day: state.house.price,
    total_price: state.house.price * Number(nightsEl.textContent),
  };

  if (tg) {
    tg.sendData(JSON.stringify(payload));
    tg.close();
    return;
  }

  alert(JSON.stringify(payload, null, 2));
});

updateSummary();
renderHouses();
render();
countryLabel.textContent = `${country.name} · ${country.city}`;
startPrice.textContent = money(Math.min(...houses.map((house) => house.price)));
