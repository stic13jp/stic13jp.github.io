#!/usr/local/bin/perl
#
# STalk 2.5 - output room report
# Copyright (C) 1999 Nobuyuki Honda (Ferdia) <ferdia@imasy.or.jp>
#

require 'stalk.cf';

$ROOMFILE = './room';

$roomnum = $ENV{'QUERY_STRING'};
$roomnum =~ tr/0-9//cd;
$line = 0;

# Count Lines
open (F, "$ROOMFILE$roomnum") || die "$ROOMFILE$roomnum: $!\n";
$line += $buf =~ tr/\n/\n/ while read(F, $buf, 65536);
close(F);

open(F, "$TAIL -50 $ROOMFILE$roomnum |") || die "$ROOMFILE$roomnum: $!\n";
@buf = <F>;
close(F);
foreach (@buf) {
    ($name, $msg, $date, $email, $ip) = split(/>/, $_);
    $list{$email} = sprintf("%-16s %-20s <A href=\"mailto:%s\">%s</A>",
			    $date, $name, $email, $email);
}
$lists = join("\n", reverse(sort(values(%list))));
$nowtime = localtime;

print <<EOF;
Content-type: text/html; charset=EUC-JP

<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=EUC-JP">
<link rel="stylesheet" type="text/css" href="../default.css" />
<title>STalk Room Report</title>
</head>
<body>
<h3>STalk Room Report</h3>
<h4>Room $roomnum: $ROOM_NAME[$roomnum] ($line lines)</h4>
<dl>
<dt>Last 50 message authors:</dt>
<dd>
<pre>
$lists
</pre>
</dd>
</dl>
<hr />
<div>$nowtime</div>
</p>
</body>
</html>
EOF
