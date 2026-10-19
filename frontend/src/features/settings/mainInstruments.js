// Contract names and stop distances come from the user's reference list.
export const MAIN_INSTRUMENT_GROUPS = [
  {
    name: "Товарная секция",
    instruments: [
      {
        name: "Нефть",
        contract: "BR-10.26",
        continuous: "RUS:BR1!",
        underlying: ["OANDA:BCOUSD"],
        averageStop: "30–50 центов",
      },
      {
        name: "Золото",
        contract: "GOLD-12.26",
        continuous: "RUS:GD1!",
        underlying: ["OANDA:XAUUSD"],
        averageStop: "5–10 долларов",
      },
      {
        name: "Серебро",
        contract: "SILV-12.26",
        continuous: "RUS:SV1!",
        underlying: ["OANDA:XAGUSD"],
        averageStop: "25–40 центов",
      },
      {
        name: "Натуральный газ",
        contract: "NG-9.26",
        continuous: "RUS:NG1!",
        underlying: ["CAPITALCOM:NATURALGAS", "VANTAGE:NG", "STONEXTRADING:NATURALGASCFD"],
        averageStop: "30–40 пунктов",
      },
    ],
  },
  {
    name: "Валюты",
    instruments: [
      {
        name: "Юань",
        contract: "CNY-12.26",
        continuous: "RUS:CR1!",
        underlying: ["RUS:CNYRUB_TOM"],
        averageStop: "50–100 пунктов (0,5–1 рубль)",
      },
      {
        name: "Доллар / рубль (Si)",
        contract: "Si-12.26",
        continuous: "RUS:SI1!",
        underlying: ["RUS:USDRUB_TOM"],
        averageStop: "50–100 пунктов (0,5–1 рубль)",
      },
    ],
  },
  {
    name: "Российский рынок",
    instruments: [
      {
        name: "Индекс Мосбиржи",
        contract: "MIX-12.26",
        continuous: "RUS:MX1!",
        underlying: ["RUS:IMOEX"],
        averageStop: "500 пунктов",
      },
    ],
  },
];
