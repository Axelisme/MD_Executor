# Arch 安裝

>Arch linux 的安裝流程，含非必要的個人喜好軟體 [name=Axelisme]
>https://github.com/Axelisme/Arch_Setup.git

## Arch 安裝I  （Live USB）

### 調大tty字體
```bash=
#%% {}
setfont ter-132n
```

### 連網路
```bash=
#確認連線狀態
#%% {}
ping 8.8.8.8

#如果要連wifi
#%% {"NotExec":[]}
iwctl    #進入iwctl界面
device list    #列出網卡硬體
station wlan0 scan    #掃描網卡wlan0底下偵測到的wifi
station wlan0 get-networks    #顯示網卡wlan0底下偵測到的wifi
station wlan0 connect "wifi"    #用網卡wlan0連接"wifi"
exit    #離開iwctl界面
```

### 更新系統時間
```bash=
#%% {"NotExec":[]}
timedatectl set-ntp true
```

### 劃分磁碟分區
```bash=
#%% {"NotExec":[]}
lsblk    #顯示磁碟分區狀態
gdisk /dev/the_disk_to_be_partitioned    #進入磁碟the_disk_to_be_partitioned
x    #專家模式
z    #刪除所有分區
cfdisk /dev/the_disk_to_be_partitioned    #圖形化分割磁碟the_disk_to_be_partitioned
```

### 格式化磁碟分區
```bash=
#%% {"NotExec":[]}
mkfs.fat -F 32 /dev/efi_system_partition    #EFI分區格式化成Fat32
mkswap /dev/swap_partition    #格式化swap
mkfs.btrfs /dev/root_partition    #格式化root分區成btrfs(也可以用ext4)
mkfs.btrfs /dev/home_partition    #格式化home分區成btrfs(也可以用ext4)
```

### 掛載磁碟分區(use btrfs)
```bash=
#%% {"NotExec":[]}
#創建資料夾
mkdir /mnt/btrfs_root
mkdir /mnt/btrfs_home
mkdir /mnt/root
#掛載btrfs磁碟到/mnt/btrfs_xx
mount /dev/root_partition /mnt/btrfs_root
mount /dev/home_partition /mnt/btrfs_home
#建立子捲
btrfs subvolume create /mnt/btrfs_root/@
btrfs subvolume create /mnt/btrfs_home/@home
#掛載
mount /dev/root_partition -o subvol=@ /mnt/root
mkdir /mnt/root/boot
mkdir /mnt/root/home
mount /dev/efi_system_partition /mnt/root/boot    #EFI分區掛載到/mnt/boot
mount /dev/home_partition -o subvol=@home /mnt/root/home
swapon /dev/swap_partition    #掛載swap分區
#為不想備份到的部份建立子捲
btrfs sub create /mnt/root/tmp
```

### 安裝系統
```bash=
#%% {"NotExec":[]}
pacman -Syy    #更新資料庫
#%%* {"kernel":["linux", "linux-lts", "linux-zen"]}
#%% {"NotExec":[]}
pacstrap /mnt/root base linux-firmware {kernel}    #安裝基礎包
#%%* {"NotExec":[],"CPU":["amd", "intel"]}
#%% {"NotExec":[]}
pacstrap /mnt/root {CPU}-ucode    #安裝Intel微碼（只有Intel CPU要裝）
#pacstrap /mnt/root amd-ucode     #安裝AMD微碼（只有AMD CPU要裝）
```

### 設定開機引導文件
```bash=
#%% {"NotExec":[]}
genfstab -U /mnt/root >> /mnt/root/etc/fstab    #Fstab引導開機系統掛載

#%% {"filesystem":"btrfs"}
#%% {"NotExec":[]}
#if use btrfs, then
nano /mnt/root/etc/fstab
#給root與home分區加上
# autodefrag,compress=zstd
# relatime改成noatime
```

### 改變root位置
```bash=
#%% {"NotExec":[]}
arch-chroot /mnt/root          #把新裝的系統掛為root
```

### 必要軟體
```bash=
#%% {}
pacman -S vi vim nano          #基礎文字編輯
pacman -S networkmanager       #網路管理
pacman -S bash-completion      #bash自動補字
pacman -S terminus-font        #tty字體
```

### 設定系統
```bash=
#%% {}
#時區
ln -sf /usr/share/zoneinfo/Asia/Taipei /etc/localtime    #設置時區
hwclock --systohc                                        #同步時區

# 設定系統語言
nano /etc/locale.gen    #編輯語言庫
# 將要啟用的語言取消註解，如en_US、zh_TW
locale-gen              #生成語言資料
nano /etc/locale.conf    
# 添加
# LANG=en_US.UTF-8

#%%* {"hostname":".+"}
#設定主機名，"myhostname"可替換成想要的名字
echo "{hostname}" >> /etc/hostname

#%% {}
#設定root密碼
passwd
```

### 安裝開機引導Grub
```bash=
#%% {}
# if use grub-btrfs, it is recommend to read:
# https://github.com/Antynea/grub-btrfs/blob/master/initramfs/readme.md
pacman -S grub efibootmgr           #Grub
grub-install --target=x86_64-efi --bootloader-id=GRUB --efi-directory=/boot

#%% {"filesystem":"btrfs"}
systemctl enable grub-btrfsd
pacman -S grub-btrfs inotify-tools  #Grub-btrfs

#%% {}
cp /etc/default/grub /etc/default/grub.backup
nano /etc/default/grub
#TIMEOUT改成1即可
#GRUB_CMDLINE_LINUX_DEFAULT改為
# "... nowatchdog ..." 並且去除quiet
#intel太新的CPU有bug，若重開機時Load Kernal fail，要再加上"ibt=off"
grub-mkconfig -o /boot/grub/grub.cfg
```

### 啟動服務
```bash=
#%% {}
systemctl enable NetworkManager    #啟動網路服務
systemctl enable fstrim.timer      #照顧SSD硬碟
```

### 結束安裝
```bash=
#%% {}
exit    #離開chroot
umount -R /mnt/root
umount -R /mnt/btrfs_root
umount -R /mnt/btrfs_home
shutdown now 
```






## Arch 安裝II （TTY root）

### 字體調大
```bash=
#%% {"word_size": ["big", "small"]}
#%% {"word_size": "big"}
setfont ter-132n
```

### 連網路
```bash=
#%% {}
#確認連線狀態
ping 8.8.8.8

#如果需要設定連網
#%% {"NotExec":[]}
nmtui    #進入networkmanager TUI
```

### pacman 設定
```bash=
#%% {}
cp /etc/pacman.conf /etc/pacman.conf.backup
nano /etc/pacman.conf
# misc options 下
: '
Color
ParallelDownloads = 5
ILoveCandy
UseSyslog
CheckSpace
VerbosePkgLists
'
# 取消註解multilib
```

### 更新
```bash=
#%% {}
pacman -Syyu
```

### 讓make使用多核編譯
```bash=
#%% {}
cp /etc/makepkg.conf /etc/makepkg.conf.backup
sudo sed -i 's/^MAKEFLAGS=".*"/MAKEFLAGS="-j$(nproc)"/1' /etc/makepkg.conf
nano /etc/makepkg.conf 
#let MAKEFLAGS="-j$(nproc)"
```

### 重要軟體
```bash=
#%% {}
pacman -S sudo                         # 管理者權限
pacman -S linux-zen-headers base-devel #linux標頭檔、編譯基礎工具
pacman -S mesa                         #顯卡渲染驅動（intel & AMD）
pacman -S lm_sensors                   #設備狀況監控
pacman -S git openssh man              #開發工具（git、ssh通訊協定、man顯示指令說明）
pacman -S fakeroot                     #fakeroot
pacman -S make gcc                     #編譯C相關
pacman -S python python-pip            #Python相關
pacman -S wget                         #其他
pacman -S alsa-utils pipewire pipewire-pulse pipewire-alsa pipewire-jack #音效
#pacman -S spice-vdagent               #虛擬機Guest用
# systemctl enable sshd                  #啟動ssh伺服器

#%% {"CPU":"intel"}
pacman -S intel-media-driver vulkan-intel    #Intel GPU硬件視頻加速、3D渲染加速（只適用Intel）
#%% {"CPU":"amd"}
pacman -S libva-mesa-driver mesa-vdpau xf86-video-amdgpu vulkan-radeon    #AMD GPU硬件視頻加速、3D渲染加速（只適用AMD）
```

### Nvidia顯示卡(if use nvidia card)
請務必詳閱:
* https://wiki.archlinux.org/title/NVIDIA
* https://wiki.archlinux.org/title/PRIME
* https://wiki.archlinux.org/title/NVIDIA/Tips_and_tricks

```bash=
#Check kernel config have CONFIG_DRM_SIMPLEDRM=y, linux-zen has checked
zcat /proc/config.gz | less  

#%% {"GPU":["nvidia", "amd", "intel"]}
#%% {"GPU":"nvidia","kernel":"linux-[^(?:lts)]"}
pacman -S dkms               #動態模塊管理
pacman -S nvidia-dkms        #nvidia driver如果kernel用linux，nvidia-dkms改成nvidia

#%% {"GPU":'"nvidia","kernel":"linux"}
pacman -S nvidia

#%% {"GPU":"nvidia","kernel":"linux-lts"}
pacman -S nvidia-lts

#%% {"nvidia-prime":["True", "False"]}
#%% {"GPU":"nvidia", "nvidia-prime":"True"}
pacman -S nvidia-prime       #筆記本切換顯卡用
systemctl enable nvidia-persistenced.service #for nvidia prime
#pacman -S nvidia-settings    #設定Nvidia configure
```

### Mkinitcpio設定
```bash=
#%% {}
#有用Nvidia或Grub-btrfs需要更改mkinitcpio.conf
cp /etc/mkinitcpio.conf /etc/mkinitcpio.conf.backup 
nano /etc/mkinitcpio.conf
#Set
# MODULES=(i915 nvidia nvidia_modeset nvidia_uvm nvidia_drm)  #Nvidia
# HOOKS=(base ... modconf ... fsck)    去除kms #Nvidia
# HOOKS=(base ... modconf ... fsck grub-btrfs-overlayfs) # Grub-btrfs

mkinitcpio -p {kernel}
```

### Grub設定
```bash=
#%% {}
nano /etc/default/grub
# GRUB_TIMEOUT="1"
#GRUB_CMDLINE_LINUX_DEFAULT改為
#去除quiet
# "... nvidia_drm.modeset=1" （有用Nvidia時才要加）
#intel太新的CPU有bug，若重開機時Load Kernal fail，要再加上"ibt=off"
grub-mkconfig -o /boot/grub/grub.cfg
```

### 建立一般使用者帳戶並修改密碼
```bash=
#%% {"user_name": ".+"}
useradd -m -g users -G wheel -s /bin/bash {user_name}    #創名為axel的用戶
passwd {user_name}    #更改用戶axel的密碼

#%% {}
visudo    #編輯群組權限（取消註解wheel:(ALL) ALL）
```

### 登出root
```bash=
#%% {}
exit
```

## Arch 安裝III（TTY user）

### KDE
```bash=
#%% {}
sudo pacman -S xorg-server            #X11 session
sudo pacman -S sddm                   #登入管理器
sudo systemctl enable sddm.service    #啟動KDE登錄畫面引導
sudo pacman -S plasma                 #kde 桌面
sudo pacman -S kde-applications       #kde 搭配軟體
```
一些kde-applications可用軟體清單
| 編號 | 名稱             | 推薦度（🡫） | 描述                        |
| ---- | ---------------- | ------------ | --------------------------- |
| 5    | ark              | 1            | 壓縮軟體                    |
| 13   | color-kde        | 0            | 桌面色彩管理                |
| 14   | dolphin          | 1            | 檔案管理                    |
| 15   | dolphin-plugins  | 1            | dolphin插件                 |
| 17   | elisa            | 2            | 音樂專輯播放器              |
| 19   | ffmpegthumbs     | 1            | 讓檔案瀏覽器預覽影片        |
| 20   | filelight        | 1            | 查看硬碟使用空間            |
| 23   | gwenview         | 1            | 看圖軟體                    |
| 34   | kamoso           | 3            | 電腦相機拍照                |
| 38   | kate             | 1            | 文字編輯器                  |
| 47   | kcalc            | 2            | 小計算機                    |
| 48   | kcharselect      | 2            | 特殊符號選擇庫              |
| 54   | kdekonnect       | 1            | 多裝置之間連線傳檔案        |
| 57   | kdenlive         | 3            | 影片剪輯工具                |
| 64   | kdf              | 1            | 硬碟使用檢視                |
| 68   | kfind            | 3            | 檔案尋找軟體                |
| 76   | khelpcenter      | 2            | KDE軟體說明文件             |
| 107  | kolourpaint      | 2            | 小畫家                      |
| 111  | konsole          | 1            | 終端機                      |
| 128  | ksystemlog       | 1            | 查看systemlog               |
| 131  | ktorrent         | 3            | torrent種子下載器           |
| 136  | kwalletmanager   | 1            | 電腦秘要權限管理？          |
| 145  | okular           | 1            | PDF閱讀軟體                 |
| 148  | partitiomanager  | 1            | 磁碟分割管理                |
| 158  | spectacle        | 1            | 螢幕節圖軟體                |
| 175  | yakuake          | 1            | 下拉型終端機                |



### 藍芽
```bash=
#%% {}
sudo pacman -S bluez bluez-utils
sudo systemctl enable bluetooth.service
```

### 字體
```bash=
#%% {}
sudo pacman -S noto-fonts-cjk    #亞洲字體
sudo pacman -S noto-fonts-emoji    #顏文字
# sudo pacman -S noto-fonts-extra    #少數字
```

### Firefox
```bash=
#%% {}
sudo pacman -S firefox                #上網
```

### 重新開機
```bash=
#%% {}
reboot
```

## Arch 安裝IV（KDE user）
先登入firefox同步後比較方便

### 排序mirror list
請參考 https://wiki.archlinux.org/title/mirrors
mirror可從 https://archlinux.org/mirrorlist/ 獲得
```bash=
#%% {}
sudo pacman -S pacman-contrib         #rankmirrors command
sudo cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.backup
echo '
## Taiwan
Server = https://free.nchc.org.tw/arch/$repo/os/$arch
Server = https://archlinux.cs.nycu.edu.tw/$repo/os/$arch
Server = http://ftp.tku.edu.tw/Linux/ArchLinux/$repo/os/$arch
Server = http://mirror.archlinux.tw/ArchLinux/$repo/os/$arch
Server = http://archlinux.ccns.ncku.edu.tw/archlinux/$repo/os/$arch
Server = https://mirror.archlinux.tw/ArchLinux/$repo/os/$arch
' | sudo tee -a /etc/pacman.d/mirrorlist.backup
rankmirrors /etc/pacman.d/mirrorlist.backup | sudo tee /etc/pacman.d/mirrorlist

sudo pacman -Syyu    #更新pacman的mirrorlist
```

### Yay(AUR管理指令)
```bash=
#%% {}
#yay
cd ~/Downloads
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si
cd
yay -Y --combinedupgrade --batchinstall --devel --save
yay --noeditmenu --nodiffmenu --save
yay -Y --gendb
```

### 掛載外部btrfs硬碟的預設參數
```bash=
#%% {}
echo '
[defaults]
btrfs_defaults=noatime,space_cache=v2,compress=zstd
btrfs_allow=noatime,space_cache,compress,compress-force,datacow,nodatacow,datasum,nodatasum,degraded,device,discard,nodiscard,subvol,subvolid
' | sudo tee -a /etc/udisks2/mount_options.conf
```

### nvidia 後續
```bash=
#%% {"GPU":"nvidia", "nvidia-prime":"True"}
# for nvidia-prime
echo '
# Enable runtime PM for NVIDIA VGA/3D controller devices on driver bind
ACTION=="bind", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x030000", TEST=="power/control", ATTR{power/control}="auto"
ACTION=="bind", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x030200", TEST=="power/control", ATTR{power/control}="auto"

# Disable runtime PM for NVIDIA VGA/3D controller devices on driver unbind
ACTION=="unbind", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x030000", TEST=="power/control", ATTR{power/control}="on"
ACTION=="unbind", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x030200", TEST=="power/control", ATTR{power/control}="on"
' | sudo tee -a /etc/udev/rules.d/80-nvidia-pm.rules

#%% {"GPU": "nvidia"}
# improve performanace
echo '
options nvidia-drm modeset=1
options nvidia NVreg_UsePageAttributeTable=1
' | sudo tee -a /etc/modprobe.d/nvidia.conf

#%% {"GPU":"nvidia", "nvidia-power-save":["True","False"]}
#%% {"GPU":"nvidia", "nvidia-power-save":"True"}
#筆電省電用
echo '
options nvidia NVreg_DynamicPowerManagement=0x02
' | sudo tee -a /etc/modprobe.d/nvidia.conf
```

### 顯卡Hook設定
```bash=
#%% {"GPU":"nvidia"}
sudo sed -i 's/^#HooDir/HooDir/1' /etc/pacman.conf  #取消註解HooDir
sudo mkdir /etc/pacman.d/hooks/
#請確保Target是自己裝的nvidia版本（如nvidia或nvidia-lts...之類）
echo "
[Trigger]
Operation=Install
Operation=Upgrade
Operation=Remove
Type=Package
Target=nvidia
Target={kernel}
# Change the linux part above and in the Exec line if a different kernel is used

[Action]
Description=Update NVIDIA module in initcpio
Depends=mkinitcpio
When=PostTransaction
NeedsTargets
Exec=/bin/sh -c 'while read -r trg; do case $trg in linux) exit 0; esac; done; /usr/bin/mkinitcpio -P'
" | sudo tee /etc/pacman.d/hooks/nvidia.hook
```

### Intel顯卡設定
```bash=
#%% {"CPU":"intel"}
# 相關資訊請看 https://wiki.archlinux.org/title/Intel_graphics
echo "\
options i915 enable_guc=3   #硬體加速
options i915 enable_fbc=1   #幀緩沖壓縮
options i915 fastboot=1     #快速啟動
" | sudo tee -a /etc/modprobe.d/i915.conf
```

### Manual setup
手動設定桌面：
* krohnkite: 從設定中安裝，可參考 https://github.com/esjeon/krohnkite
* autocomposor: 從設定中安裝
* grub theme: https://www.gnome-look.org/browse?cat=109
* yakuake自定義：快捷鍵、透明
* firefox sync
* desktop theme
* login theme
* font size
* desktop background
* number lock on
* desktop widgets
* btrfs-assistant setup
* other btrfs subvolume

對於krohnkite請另外執行
```bash=
mkdir -p ~/.local/share/kservices5/
ln -s ~/.local/share/kwin/scripts/krohnkite/metadata.desktop ~/.local/share/kservices5/krohnkite.desktop
```

### 其他
其餘請參見Arch快速設定
https://hackmd.io/@Axelisme/SJJay80os/edit

# 有用的網站

https://hackmd.io/@PIFOPlfSS3W_CehLxS3hBQ/r1xrYth9V

https://ivonblog.com/posts/install-archlinux/

https://zhao.center/post/archlinux-install-note-beginner/#install-base-package

https://hackmd.io/@B083040012/SkrsJkpgt#Arch-Linux-%E5%AE%89%E8%A3%9D%E5%BE%8C%E5%B7%A5%E4%BD%9C