COMMODITIES=(
"all"
"Live animals/fish"
"Cereal grains"
"Other ag prods."
"Animal feed"
"Meat/seafood"
"Milled grain prods."
"Other foodstuffs"
"Alcoholic beverages"
"Tobacco prods."
"Building stone"
"Natural sands"
"Gravel"
"Nonmetallic minerals"
"Metallic ores"
"Coal"
"Crude petroleum"
"Gasoline"
"Fuel oils"
"Natural gas and other fossil products"
"Basic chemicals"
"Pharmaceuticals"
"Fertilizers"
"Chemical prods."
"Plastics/rubber"
"Logs"
"Wood prods."
"Newsprint/paper"
"Paper articles"
"Printed prods."
"Textiles/leather"
"Nonmetal min. prods."
"Base metals"
"Articles-base metal"
"Machinery"
"Electronics"
"Motorized vehicles"
"Transport equip."
"Precision instruments"
"Furniture"
"Misc. mfg. prods."
"Waste/scrap"
"Mixed freight"
)

REGIONS=(
all
11
12
19
20
41
42
49
50
61
62
63
64
65
69
81
89
91
92
99
101
109
111
121
122
123
124
129
131
132
139
151
159
160
171
172
179
181
182
183
189
190
201
202
209
211
212
219
221
222
223
229
230
241
242
249
251
259
261
262
269
271
279
280
291
292
299
300
311
319
321
329
331
339
341
342
350
361
362
363
364
369
371
372
373
379
380
391
392
393
394
399
401
402
409
411
419
421
422
423
429
441
451
452
459
460
471
472
473
479
481
482
483
484
485
486
487
488
489
491
499
500
511
512
513
519
531
532
539
540
551
559
560
)

#MODES=(all truck water rail)
MODES=(truck)

# Calculate the total number of jobs to run
total_jobs=$((${#MODES[@]} * ${#REGIONS[@]} + ${#MODES[@]} * ${#COMMODITIES[@]}))

i=1
for mode in "${MODES[@]}"; do

  # Run through each set of origin/destination regions for all commodities
  for region in "${REGIONS[@]}"; do
    echo python source/Point2PointFAF.py -m truck -o ${region}
    python source/Point2PointFAF.py -m truck -o ${region} &> Logs/truck_origin_origin${region}.txt &
    python source/Point2PointFAF.py -m truck -d ${region} &> Logs/truck_destination_dest${region}.txt &

    if ! ((i % 8)); then
        echo Pausing to let jobs finish
        wait
    fi

    i=$((i+1))
    echo Processed $i jobs of ${total_jobs}
  done
  
  # Run through each commodity for all regions
  for commodity in "${COMMODITIES[@]}"; do
    commodity_save=$(echo "${commodity}" | tr '/' '_' | tr ' ' '_')
    echo python source/Point2PointFAF.py -m truck -c "${commodity}"
    python source/Point2PointFAF.py -m truck -c "${commodity}" &> Logs/truck_origin_commodity_"${commodity_save}".txt &
  
    if ! ((i % 8)); then
        echo Pausing to let jobs finish
        wait
    fi
  
    echo Processed $i jobs of ${total_jobs}
    i=$((i+1))
  done
done
