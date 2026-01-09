{
  "inheritanceType": "autosomal_recessive",
  "people": [
    {
      "id": "g1",
      "name": "Grandfather",
      "sex": "male",
      "generation": 1,
      "status": "unknown",
      "carrier_probability": null
    },
    {
      "id": "g2",
      "name": "Grandmother",
      "sex": "female",
      "generation": 1,
      "status": "unknown",
      "carrier_probability": null
    },
    {
      "id": "p1",
      "name": "Father",
      "sex": "male",
      "generation": 2,
      "status": "unaffected",
      "carrier_probability": null
    },
    {
      "id": "p2",
      "name": "Mother",
      "sex": "female",
      "generation": 2,
      "status": "carrier",
      "carrier_probability": null
    },
    {
      "id": "c1",
      "name": "Child 1",
      "sex": "male",
      "generation": 3,
      "status": "unknown",
      "carrier_probability": null
    },
    {
      "id": "c2",
      "name": "Child 2",
      "sex": "female",
      "generation": 3,
      "status": "unknown",
      "carrier_probability": null
    }
  ],
  "relationships": [
    { "parent": "g1", "child": "p1" },
    { "parent": "g2", "child": "p1" },
    { "parent": "p1", "child": "c1" },
    { "parent": "p2", "child": "c1" },
    { "parent": "p1", "child": "c2" },
    { "parent": "p2", "child": "c2" }
  ]
}
