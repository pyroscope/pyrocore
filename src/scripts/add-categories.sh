#! /usr/bin/env bash
#
# Add views and watches to the rTorrent condiguration,
# for the categories provided as arguments.

set -e

cat_rc="rtorrent.d/categories.rc"

touch "$cat_rc"
categories=( $({ grep pyro.category.add "$cat_rc" | tr -d ' ' | \
                 cut -f2 -d= | egrep '^[_a-zA-Z0-9]+$'; echo "$@" | tr ' ' \\n; } | sort -u) )

cat >$cat_rc <<EOF
# Category Definitions for:
#   ${categories[@]}

# "Other" category for empty labels
pyro.category.add = (cat,)
EOF

for i in $(seq ${#categories[@]}); do
    name="${categories[$(($i - 1))]}"

    mkdir -p "watch/$name"
    echo -e >>$cat_rc \
        "\npyro.category.add = $name\nschedule2 =" \
        "category_watch_$(printf '%02d' $i), $((10 + $i)), 10," \
        "((load.category.normal, $name))"
done

cat "$cat_rc"
echo
echo "################################################"
echo "# Restart rTorrent for changes to take effect! #"
echo "################################################"
