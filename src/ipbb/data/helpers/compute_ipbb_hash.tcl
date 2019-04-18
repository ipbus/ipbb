puts "Computing ipbb project hash"

if {[catch {exec bash -c "ipbb --version"} results options]} {
    set details [dict get $options -errorcode]
    if {[lindex $details 0] eq "CHILDSTATUS"} {
        set status [lindex $details 2]

        puts "ERROR: ipbb not found. Impossible to calculate the project hash."
        return -code error -errorinfo "ipbb not found" -errorcode "-999"

    } else {
        # Some other error; regenerate it to let caller handle
        return -options $options -level 0 $results
    }
}
puts "Detected: $results"

exec bash -c "cd [get_property DIRECTORY [current_project]]; ipbb info"
set ipbb_hash [exec bash -c "cd [get_property DIRECTORY [current_project]]; ipbb dep hash"]
puts "Project hash: $ipbb_hash"
