#!/usr/local/bin/perl
#
# STalk 2.5.2 (1999-06-12)
# Copyright (C) 1999 Nobuyuki Honda (Ferdia) <ferdia@imasy.or.jp>
# Freely redistributable. Absolutely no warranty.
#
require 5.003;
require 'jcode.pl';
use strict;

# config
use vars qw(
    $TAIL $ADMIN @ROOM_NAME @ROOM_DESC
    $ENTERANCEHEAD  $ENTERANCEFOOT $ROOMHEAD $ROOMFOOT
    $VERSION  $STALK_URL
);
# global
my(
    $STALKSCRIPT, $REPORTSCRIPT, $COOKIENAME, $COOKIE_EXPIRES, $CONFFILE,
    $HELPFILE, $ROOMFILE, $DEFAULTLINE, %FORM, @ROOMDATE
);

$VERSION	= '2.5.2';
$STALK_URL	= 'http://www.imasy.or.jp/~ferdia/stalk/';
$STALKSCRIPT	= 'stalk.cgi';
$REPORTSCRIPT	= 'stalk-report.cgi';
$CONFFILE	= 'stalk.cf';
$HELPFILE	= 'stalk-help.html';
$ROOMFILE	= './room';
$COOKIENAME	= 'STalk';
$COOKIE_EXPIRES = 'Monday, 18-Feb-30 00:00:00 GMT';
$DEFAULTLINE	= 20;

require 'stalk.cf';

#--------------------------------------------------------------------
# URL encode
#--------------------------------------------------------------------
sub escape($)
{
    my $toencode = shift;
    return undef unless defined($toencode);
    $toencode =~ s/([^a-zA-Z0-9_.-])/uc sprintf("%%%02x",ord($1))/eg;
    return $toencode;
}

#--------------------------------------------------------------------
# decode URL encoded data
#--------------------------------------------------------------------
sub unescape($)
{
    my $todecode = shift;
    $todecode =~ tr/+/ /;
    $todecode =~ s/%([a-fA-F0-9]{2})/pack("C", hex($1))/eg;
    return $todecode;
}

#--------------------------------------------------------------------
# escape HTML
#--------------------------------------------------------------------
sub escapeHTML($)
{
    my $toencode = shift;
    return undef unless defined($toencode);
    $toencode =~ s/\&/\&amp;/g;
    $toencode =~ s/\</\&lt;/g;
    $toencode =~ s/\>/\&gt;/g;
    $toencode =~ s/\"/\&quot;/g;
    return $toencode;
}

#--------------------------------------------------------------------
# get Cookie data
#--------------------------------------------------------------------
sub getcookie()
{
    my ($name, $value, %cookies, @pairs);
    my $cookie = $ENV{'HTTP_COOKIE'};

    return undef unless defined($cookie);

    @pairs = split(/;/, $cookie);
    foreach (@pairs) {
   	($name, $value) = split(/=/, $_);
	$cookies{$name} = $value;
    }

    @pairs = split(/&/, $cookies{$COOKIENAME});
    foreach (@pairs) {
	($name, $value) = split(/\//, $_);
	$value = unescape($value);
	# convert to EUC-JP
	jcode::convert(*value, 'euc');
	$FORM{$name} = $value;
    }
}

#--------------------------------------------------------------------
# get input data
#--------------------------------------------------------------------
sub getinput()
{
    my($buffer, $name, $value, @pairs);
    my $meth = $ENV{'REQUEST_METHOD'};

    return unless defined($meth);

    $buffer = '';
    if ($meth eq 'POST') {
	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
    }
    $buffer .= '&' . $ENV{'QUERY_STRING'};

    @pairs = split(/&/, $buffer);
    foreach (@pairs) {
	($name, $value) = split(/=/, $_);
	$value = unescape($value);
	# convert to EUC-JP
	jcode::convert(*value, 'euc');
	$FORM{$name} = $value;
    }
}

#--------------------------------------------------------------------
# Write Message
#--------------------------------------------------------------------
sub writemessage($$$$)
{
    my($roomnum, $email, $name, $msg,) = @_;
    my($min, $hour, $mday, $mon, $year) = (localtime)[1..5];

    open(F, ">> $ROOMFILE$roomnum") || die "$ROOMFILE$roomnum: $!\n";
    flock(F, 2);
    printf F "%s>%s>%d/%02d/%02d %02d:%02d>%s>%s>\n",
	escapeHTML($name), escapeHTML($msg),
	$year+1900, $mon+1, $mday, $hour, $min,
	escapeHTML($email), $ENV{'REMOTE_ADDR'};
    flock(F, 8);
    close(F);
}

#--------------------------------------------------------------------
# Print Message
#--------------------------------------------------------------------
sub printmsg($$)
{
    my($rnum, $line) = @_;
    my($name, $msg, $date, $mail);

    if ($line == -1) {	# print all message
	open(F, "$ROOMFILE$rnum") || die "$ROOMFILE$rnum: $!\n";
    }
    else {
	open(F,"$TAIL -$line $ROOMFILE$rnum |") || die "$ROOMFILE$rnum: $!\n";
    }
    while (<F>) {
	($name, $msg, $date, $mail) = split(/>/, $_);
	$msg =~ s{([a-z0-9+\-.]+://[a-zA-Z0-9\$\-_.+!*'(),;/?:@&=%~#]+)}
		 {<a href="$1">$1</a>}g;
	print qq{<table width="100%" cellspacing="0"><tr valign="top"><td width="15%">[<a href="mailto:$mail">$name</a>]</td><td>$msg <small>($date)</small></td></tr></table>\n};
	#print qq{<TABLE WIDTH="100%" CELLSPACING=0><TR VALIGN=TOP><TD WIDTH="25%"><SMALL>$date</SMALL> [<A HREF="mailto:$mail">$name</A>]<TD>$msg</TABLE>\n};
	#print qq{[<A HREF="mailto:$mail">$name</A>] <DIV STYLE="margin: -1em 0 0 8em">$msg <SMALL>($date)</SMALL></DIV><BR>\n};
    }
    close(F);
}

#--------------------------------------------------------------------
# Enter Room Form & Room List
#--------------------------------------------------------------------
sub printenterance($$)
{
    my($i, $roomsel, $min, $hour, $mday, $mon, $year, $mtime);
    my $roomlist = '';
    my $email = escapeHTML(shift);
    my $name = escapeHTML(shift);

    # make room list
    for ($i = 1; $i <= $#ROOM_NAME; $i++) {
        ($min, $hour, $mday, $mon, $year) = (localtime($ROOMDATE[$i]))[1..5];
        $mtime = sprintf("%d/%02d/%02d %02d:%02d",
			 $year+1900, $mon+1, $mday, $hour, $min);
	$roomlist .= qq{
		<dt><input type="submit" name="r" value="Room $i">
		$ROOM_NAME[$i] - $ROOM_DESC[$i] ($mtime)
	};
    }

    # HTML Output
    print <<EOF;
	$ENTERANCEHEAD
	<form action="$STALKSCRIPT" method="get">
	<dl>
	<dt>Name: <input name="n" size="18" maxlength="16" value="$name">
		(max 16 characters)
	<dt>mail: <input name="e" size="36" value="$email">
	</dl>
	<p><input type="submit" name="c" value="Set">
	name and mail address in your browser (use COOKIE).
	</p>
	<dl>
	$roomlist
	</dl>
	</form>
	$ENTERANCEFOOT
EOF
}

#--------------------------------------------------------------------
# Room & Input Form
#--------------------------------------------------------------------
sub printroom($$$$$)
{
    my($roomnum, $email, $name, $line, $canwrite) = @_;
    my($i, $min, $hour, $mday, $mon, $year, $mtime, $s, $roomsel);
    my $encname = escape($name);
    my $encemail = escape($email);
    $name = escapeHTML($name);
    $email = escapeHTML($email);

    # make room select
    for ($i = 1; $i < @ROOM_NAME; $i++) {
        ($min,$hour,$mday,$mon,$year) = (localtime($ROOMDATE[$i]))[1..5];
        $mtime = sprintf("%d/%02d/%02d %02d:%02d",
			 $year+1900, $mon+1, $mday, $hour, $min);
	if ($i == $roomnum) { $s = ' selected' } else { $s = '' }
  	$roomsel .= "<option value=\"$i\"$s>Room $i: $ROOM_NAME[$i] ($mtime)\n\t";
    }

    # HTML Output
    print <<EOF;
	$ROOMHEAD
	<h3>Room $roomnum: $ROOM_NAME[$roomnum] - $ROOM_DESC[$roomnum]</h3>
	<form action="$STALKSCRIPT" method="get">
	<select name="r" onchange="submit()">
	<option value="0">Entrance
	$roomsel</select>
	<input type="submit" value=" Go ">
	| <a href="$REPORTSCRIPT?$roomnum">room report</a>
	| <a href="$HELPFILE">help</a> |
	<input type="hidden" name="n" value="$name">
	<input type="hidden" name="e" value="$email">
	</form>
EOF

    printmsg($roomnum, $line);

    # Input Form
    print <<EOF if $canwrite;
	<form action="$STALKSCRIPT?r=$roomnum&n=$encname&e=$encemail" name="inputform" method="POST">
	<table width="100%" cellspacing="0">
	<tr><td width="15%">[<a href="mailto:$email">$name</a>]</td>
	<td width="85%" colspan="2"><input type="text" name="m" size="100">
	<input type="submit" value="Send"></td></tr>
	</table>
	</form>
	<script type="text/javascript">
	<!--
	document.inputform.m.focus();
	//-->
	</script>
EOF
    print $ROOMFOOT;
}

#--------------------------------------------------------------------
# MAIN
#--------------------------------------------------------------------
main();
sub main()
{
    my($roomnum, $name, $email, $msg, $line, $canwrite, $lastmod, $i);

    getcookie();
    getinput();

    $roomnum = $FORM{'r'} || 0;
    $roomnum =~ tr/0-9//cd;
    $name    = $FORM{'n'} || '';
    $email   = $FORM{'e'} || '';
    $msg     = $FORM{'m'} || '';

    if (defined($FORM{'c'})) {
	# Send Cookie
        my $encname = escape($name);
        my $encemail = escape($email);
	print "Set-Cookie: $COOKIENAME=n/$encname&e/$encemail; expires=$COOKIE_EXPIRES;\n";
    }
    print "Content-Type: text/html; charset=euc-jp\n\n";

    # get update time of room
    for ($i = 1; $i < @ROOM_NAME; $i++) {
	$ROOMDATE[$i] = (stat("$ROOMFILE$i"))[9];
    }

    # print entrance
    if ($roomnum < 1 || $roomnum > $#ROOM_NAME) {
	printenterance($email, $name);
    }
    # print room
    else {
	# check name and mail address
	$canwrite = $name && ($email =~ /^[\w.-]+\@([\w.-])+\w+$/); #from perlfaq9

	# put message
	$line = $DEFAULTLINE;
	if ($canwrite && $msg) {
	    # read all
	    if ($msg =~ m|^/ra\s*$|i) { $line = -1 }
	    # read n lines
	    elsif ($msg =~ m|^/r\s*(\d*)$|i) { $line = $1 if ($1 > 0) }
	    # write message
	    else {
		writemessage($roomnum, $email, $name, $msg);
		$ROOMDATE[$roomnum] = (stat("$ROOMFILE$roomnum"))[9];
	    }
	}
	# print room
	printroom($roomnum, $email, $name, $line, $canwrite);
    }
}
