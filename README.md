<h1 style="background: rgb(246,4,213);
background: linear-gradient(90deg, rgba(246,4,213,1) 0%, rgba(4,223,69,1) 0%, rgba(9,9,121,1) 51%, rgba(255,0,11,1) 100%);padding:1.5rem;text-align:center;" align=center>پروژه سوشال مدیا با جنگو</h1>

<p style="font-size:1.1rem">این سایت مقاله ای با جنگو نسخه۵ نوشته شده. پروژه api-base هست و با Django Rest Framework نوشته شده است و برای قسمت چت و نوتیفیکیشن از channel استفاده شده .</p>

برای دستیابی به داکیومنت پروژه بعد از اجرا کردن کد ها به مسیر `/docs/ `بروید
<p>برای اجرای کد ها این <a href="#اجرا-کردن-پروژه">مراحل</a> را پیش ببرید</p>

## قابلیت های پروژه

<ul>
<li>دیدن و اضافه کردن و ادیت و حذف پست ها و استوری ها</li>
<li>غیر فعال شدن استوری ها بعد از ۲۴ ساعت</li>
<li>قابلیت چت کردن با بقیه افراد</li>
<li>فالو یا انفالو کردن افراد</li>
<li>ارسال نوتیفیکیشن</li>
<li>لاگین و رجیستر کردن با ارسال کد به ایمیل</li>
<li>کامنت برای پست و استوری ها</li>
<li>سرچ کردن پست ها براساس تگ هر پست</li>
<li>تغییر پروفایل</li>
<li>ایجاد چند فیلم یا عکس برای یک پست یا استوری</li>

</ul>

<hr>
<br>
<br>

# اجرا کردن پروژه

<p>همانطور که میدانید این پروژه با جنگو نوشته شده و از ساختار فولدر بندی جنگو ارث بری میکند</p>

### گام اول :نصب پکیج ها

<p>بعد از دانلود سورس کد وارد پوشه کد ها بشید و برای نصب پکیج های مورد نیاز پروژه دستور پایین رو بزنین</p>

‍‍‍‍‍```pip install -r requirements.txt```
<p>لطفا تا نصب شدن پکیج ها صبر کنید ممکنه به علت هایی مثل سرعت <span style="color:yellow">بشدت بالا</span> در ایران یا مشکل فیلترینگ اندکی طول بکشه</p>

### گام دوم :ایجاد دیتابیس

با زدن این دستور دیتابیس ایجاد میشود

‍```python manage.py migrate```

### گام سوم: دستور collectstatic
<p>دستور زیر را اجرا کنید</p>

```python manage.py collectstatic```

### گام چهارم: اجرا کردن پروژه

<p>با دستور زیر پروژه رو ران کنید</p>

```python manage.py runserver```

<hr>

## ایجاد کاربر ادمین

<p>برای اینکه به پنل ادمین دسترسی داشته باشید باید یک کاربر ادمین بسازید با دستور زیر این کارو بکنید</p>

```python manage.py createsuperuser```

<p>و مقادیری که از شما خواسته میشود رو وارد کنید</p>

<hr>

##  تغییرات پروژه

<ul>
<li><span style="color:green;font-weight:bold;font-size:1.2rem">حذف redis:</span>
یک سری قابلیت ها در نسخه قبلی که توسعه دادم وجود داشت که تغییر دادم مثل استفاده از ردیس در سیستم caching و channel-layer پروژه که به علت اینکه در فرایند ران شدن پروژه یک مرحله اضافه تر میکرد و ممکن بود برای افرادی که میخان این پروژه رو ران کنن و خروجی رو ببینن سخت باشه بخاطر همین بعد ها در اپدیتی که کردم به جای ردیس از FileBasedCache استفاده کردم</li>
<br>
<li><span style="color:yellow;font-weight:bold;font-size:1.2rem">حذف celery:</span>در نسخه های اول برای سیستم بستن هر استوری بعد ۲۴ ساعت از سلری استفاده کرده بودم که برای اینکه اجرای کد راحت تر باشه و نیازی به ران کردن celery-beat celery-worker نباشه از یک قطعه کد خیلی کوتاه و بهینه تر استفاده کردم</li>
</ul>

##  اپدیت های پیش رو در  پروژه

<ul>
<li><span style="color:green;font-weight:bold;font-size:1.2rem">داکرایزر کردن و بالا اوردن پروژه بر روی nginx:</span>فایل هاشو ایجاد کردم و در اولین فرصتی که بتونم این کارارو انجام میدم</li>

<h4 align=center style="text-align:center;background-color:white; padding:1rem;background: rgb(246,4,213);
background: linear-gradient(90deg, rgba(246,4,213,1) 0%, rgba(9,9,121,1) 51%, rgba(0,212,255,1) 100%);">لطفا اگر باگ یا مشکلی در پروژه پیدا کردید ممنون میشم در قسمت issues به من اطلاع بدید</h4>