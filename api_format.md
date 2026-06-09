# Pintu Air
Base URL: https://sisteminformasibanjir.jakarta.go.id/api/report/pintuAirReports/YYYY-MM-DD?format=json
Example: https://sisteminformasibanjir.jakarta.go.id/api/report/pintuAirReports/2026-06-08?format=json
Response: 
{
"data": [
    {
        "id": 574088,
        "ketinggian": 550,
        "bukaan": null,
        "status_siaga": 4,
        "tanggal": "2026-06-08",
        "jam": "01:00:00",
        "cuaca": {
            "inisial": "T",
            "nama": "Terang"
        },
        "pintu_air": {
            "id": 6,
            "name": "Manggarai BKB",
            "aliran": "Aliran Tengah",
            "cctv": null
        }
    },
    {
        "id": 574089,
        "ketinggian": 510,
        "bukaan": null,
        "status_siaga": 4,
        "tanggal": "2026-06-08",
        "jam": "01:00:00",
        "cuaca": {
            "inisial": "T",
            "nama": "Terang"
        },
        "pintu_air": {
            "id": 7,
            "name": "Manggarai KCL",
            "aliran": "Aliran Tengah",
            "cctv": null
        }
    },
    {
        "id": 574090,
        "ketinggian": 260,
        "bukaan": null,
        "status_siaga": 4,
        "tanggal": "2026-06-08",
        "jam": "01:00:00",
        "cuaca": {
            "inisial": "T",
            "nama": "Terang"
        },
        "pintu_air": {
            "id": 5,
            "name": "PA. Karet",
            "aliran": "Aliran Tengah",
            "cctv": "http:\/\/103.140.108.110\/viewer\/cctv\/172.168.10.56.jpg?0.29867019967521324"
        }
    },
}

# Pos Pengamatan
Base URL: ht  tps://sisteminformasibanjir.jakarta.go.id/api/report/posPengamatanReports/YYYY-MM-DD?format=json
Example: https://sisteminformasibanjir.jakarta.go.id/api/report/posPengamatanReports/2026-06-08?format=json
Response: 
{
  "data": [
      {
          "id": 362953,
          "ketinggian": 80,
          "status_siaga": 4,
          "tanggal": "2026-06-08",
          "jam": "01:49:00",
          "cuaca": {
              "inisial": "T",
              "nama": "Terang"
          },
          "pos_pengamatan": {
              "id": 1,
              "name": "Pos Depok",
              "aliran": "Aliran Tengah"
          }
      },
      {
          "id": 362954,
          "ketinggian": 70,
          "status_siaga": 4,
          "tanggal": "2026-06-08",
          "jam": "01:49:00",
          "cuaca": {
              "inisial": "T",
              "nama": "Terang"
          },
          "pos_pengamatan": {
              "id": 2,
              "name": "Pos Pesanggrahan",
              "aliran": "Aliran Barat"
          }
      },
      {
          "id": 362955,
          "ketinggian": 40,
          "status_siaga": 4,
          "tanggal": "2026-06-08",
          "jam": "01:50:00",
          "cuaca": {
              "inisial": "T",
              "nama": "Terang"
          },
          "pos_pengamatan": {
              "id": 3,
              "name": "Pos Angke Hulu",
              "aliran": "Aliran Barat"
          }
      },
      {
          "id": 362956,
          "ketinggian": 40,
          "status_siaga": 4,
          "tanggal": "2026-06-08",
          "jam": "01:50:00",
          "cuaca": {
              "inisial": "T",
              "nama": "Terang"
          },
          "pos_pengamatan": {
              "id": 4,
              "name": "Pos Krukut Hulu",
              "aliran": "Aliran Tengah"
          }
      },
  ]
}   

# Rumah Pompa
Base URL: https://sisteminformasibanjir.jakarta.go.id/api/report/rumahPompaReports/YYYY-MM-DD?format=json
Example: https://sisteminformasibanjir.jakarta.go.id/api/report/rumahPompaReports/2026-06-08?format=json
Response: 
{
    "data": [
        {
            "id": 5054131,
            "total_pompa": 4,
            "pompa_operasi": 0,
            "pompa_siaga": 4,
            "tanggal": "2026-06-08",
            "jam": "00:00:00",
            "tma": 10,
            "cuaca": {
                "inisial": "T",
                "nama": "Terang"
            },
            "pompa_air": {
                "id": 8,
                "name": "Pondok Bandung",
                "kewenangan": "SUDIN SUMBER DAYA AIR JAKARTA BARAT",
                "kapasitas": 3,
                "jumlah_operator": 9,
                "jumlah_pintu_air": 1,
                "jumlah_genset": 1
            }
        },
        {
            "id": 5054132,
            "total_pompa": 2,
            "pompa_operasi": 0,
            "pompa_siaga": 2,
            "tanggal": "2026-06-08",
            "jam": "00:00:00",
            "tma": 30,
            "cuaca": {
                "inisial": "T",
                "nama": "Terang"
            },
            "pompa_air": {
                "id": 16,
                "name": "RW 08 Kedaung Kali Angke",
                "kewenangan": "SUDIN SUMBER DAYA AIR JAKARTA BARAT",
                "kapasitas": 0,
                "jumlah_operator": 9,
                "jumlah_pintu_air": 1,
                "jumlah_genset": 1
            }
        },
        {
            "id": 5054133,
            "total_pompa": 2,
            "pompa_operasi": 0,
            "pompa_siaga": 2,
            "tanggal": "2026-06-08",
            "jam": "00:00:00",
            "tma": 90,
            "cuaca": {
                "inisial": "T",
                "nama": "Terang"
            },
            "pompa_air": {
                "id": 35,
                "name": "Kali Apuran",
                "kewenangan": "SUDIN SUMBER DAYA AIR JAKARTA BARAT",
                "kapasitas": 0.75,
                "jumlah_operator": 9,
                "jumlah_pintu_air": 1,
                "jumlah_genset": 1
            }
        },
        {
            "id": 5054134,
            "total_pompa": 2,
            "pompa_operasi": 1,
            "pompa_siaga": 1,
            "tanggal": "2026-06-08",
            "jam": "00:00:00",
            "tma": 180,
            "cuaca": {
                "inisial": "T",
                "nama": "Terang"
            },
            "pompa_air": {
                "id": 24,
                "name": "Satpas Sim",
                "kewenangan": "SUDIN SUMBER DAYA AIR JAKARTA BARAT",
                "kapasitas": 1,
                "jumlah_operator": 9,
                "jumlah_pintu_air": 1,
                "jumlah_genset": 1
            }
        },