using CSV, DataFrames

df = CSV.read("fall2025.csv", DataFrame)
tally(df.Title)
dropmissing!(df, :seats_remaining)

open =  filter(row -> row.seats_remaining > 0, df)
CSV.write("summer_courses_open.csv", open)

async = filter(x -> x.instructional_mode == "Fully Online asynchronous", open)
CSV.write("summer_courses_open_async.csv", async)

has_wl = filter(x -> x.waitlist_capacity > 0, df)
CSV.write("summer_courses_waitlist.csv", has_wl)

ewrt1a = filter(x -> x.subj == "EWRT" && x.crse == "D001A" && x.waitlist_remaining > 0, df)
CSV.write("ewrt1a.csv", ewrt1a)