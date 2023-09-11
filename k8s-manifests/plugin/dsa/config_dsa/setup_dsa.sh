#!/bin/bash
num_dsa=`ls /sys/bus/dsa/devices/  | grep dsa | wc -l`
script=`basename $0`

usage() {
    cat <<HELP_USAGE

    usage: $script [-d device (dsa0/iax1/..) ] [-w num wqs] [-m wq mode (d or s)] [-e num eng]
		configures wqs

	   $script [-d device]
		disables device

	   $script <config file path>
HELP_USAGE
	exit
}

unbind() {

	case $1 in

	0)
		for ((i = 0; i < $num_dsa ; i++ ))
		do
			echo wq$did.$i > $WQ_DRV_PATH/unbind 2>/dev/null && echo disabled wq$did.$i
		done

		echo $dname  > $DEV_DRV_PATH/unbind 2>/dev/null && echo disabled $dname
		;;

	1)

		dname=`cat $config  | grep \"dev\":\"dsa  | cut -f2 -d: | cut -f1 -d, | sed -e s/\"//g`
		readarray -d a  -t tmp <<< "$dname"
		d=`echo ${tmp[1]}`

		for i in {0..7}
		do
			[[ `cat /sys/bus/dsa/devices/$dname/wq$d\.$i/state` == "enabled" ]] && sudo accel-config disable-wq $dname/wq$d\.$i
		done

		[[ `cat /sys/bus/dsa/devices/$dname/state` == "enabled" ]] && sudo accel-config disable-device $dname
		;;

	*)
		echo "unknown"
		;;
	esac
}

configure() {

	case $1 in

	0)
		for ((i = 0; i < $num_eng ; i++ ))
		do
			echo 0 > $DSA_CONFIG_PATH/$dname/engine$did.$i/group_id
		done

		for ((i = 0; i < $num_wq ; i++ ))
		do
			[ -d $DSA_CONFIG_PATH/$dname/wq$did.$i/ ] && wq_dir=$DSA_CONFIG_PATH/$dname/wq$did.$i/
			[ -d $DSA_CONFIG_PATH/wq$did.$i/ ] && wq_dir=$DSA_CONFIG_PATH/wq$did.$i/

			echo 0 > $wq_dir/block_on_fault
			echo 0 > $wq_dir/group_id
			echo $mode > $wq_dir/mode
			echo 10 > $wq_dir/priority
			echo $size > $wq_dir/size
			[[ $mode == shared ]] && echo 10 > $wq_dir/threshold
			echo "user" > $wq_dir/type
			echo "app$i"  > $wq_dir/name
		done
		;;

	1)
		sudo accel-config load-config -c $config
		;;

	*)
		echo "Unknown"
		;;
	esac
}

bind() {
	# start devices
	case $1 in
	0)
		echo $dname  > $DEV_DRV_PATH/bind && echo enabled $dname

		for ((i = 0; i < $num_wq ; i++ ))
		do
			echo wq$did.$i > $WQ_DRV_PATH/bind && echo enabled wq$did.$i
		done
		;;
	1)
		sudo accel-config enable-device  $dname

		for i in {0..7}
		do
			[[ `cat /sys/bus/dsa/devices/$dname/wq$d\.$i/size` -ne "0" ]] && sudo accel-config enable-wq $dname/wq$d\.$i
		done
		;;
	*)
		echo "Unknown"
		;;
	esac
}

do_config_file() {

	config=$1
	unbind 1
	configure 1
	bind 1

	exit
}

do_options() {
	num_wq=0
	num_eng=4

	if [[ ! $@ =~ ^\-.+ ]]
	then
	usage
	fi

	while getopts d:w:m:e: flag
	do
	    case "${flag}" in
		d)
			dname=${OPTARG}
			did=`echo $dname | awk '{print substr($0,4)}'`
			;;
		w)
			num_wq=${OPTARG}
			;;
		e)
			num_eng=${OPTARG}
			;;
		m)
			mode=${OPTARG}
			;;
		:)
			usage >&2
			;;
		*)
			usage >&2
			;;
	    esac
	done

	[ -d /sys/bus/dsa/devices/$dname ] || { echo "Invalid dev name $dname" && exit 1; }

	DSA_CONFIG_PATH=/sys/bus/dsa/devices
	DEV_DRV_PATH=/sys/bus/dsa/drivers/dsa
	WQ_DRV_PATH=$DEV_DRV_PATH
	[ -d /sys/bus/dsa/drivers/user ] && WQ_DRV_PATH=/sys/bus/dsa/drivers/user

	if [ "$num_wq" -ne "0" ]
	then
		[[ $mode == "d" ]] && mode=dedicated
		[[ $mode == "s" ]] && mode=shared
		[[ $mode == "" ]] && usage

		wq_size=`cat /sys/bus/dsa/devices/$dname/max_work_queues_size`
		size=$(( wq_size / num_wq ))

		unbind 0
		configure 0
		bind 0
	else
		echo "disabling device" $dname
		unbind 0
	fi

	exit
}

if [ $# -eq "0" ]
then
	usage
elif [ -f "$1" ]
then
	do_config_file $1
else
	do_options $@
fi
