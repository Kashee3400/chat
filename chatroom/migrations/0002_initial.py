# Generated by Django 4.1.13 on 2025-02-20 06:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chatroom', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='textmessage',
            name='sender',
            field=models.ForeignKey(help_text='The user who sent the message', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Sender'),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_categories', to='chatroom.category'),
        ),
        migrations.AddField(
            model_name='state',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='states', to='chatroom.country'),
        ),
        migrations.AddField(
            model_name='roommessage',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_rooms', to='chatroom.subcategory'),
        ),
        migrations.AddField(
            model_name='roommessage',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_room_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='readreceipt',
            name='message',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_receipts', to='chatroom.textmessage', verbose_name='Message'),
        ),
        migrations.AddField(
            model_name='readreceipt',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='reaction',
            name='message',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='chatroom.textmessage', verbose_name='Message'),
        ),
        migrations.AddField(
            model_name='reaction',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='mediatype',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='mediatype',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AddField(
            model_name='mediasettings',
            name='media_type',
            field=models.ForeignKey(help_text='The type of media to restrict', on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='chatroom.mediatype', verbose_name='Media Type'),
        ),
        migrations.AddField(
            model_name='mediafile',
            name='message',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media_files', to='chatroom.textmessage', verbose_name='Message'),
        ),
        migrations.AddField(
            model_name='directmessageuser',
            name='friends',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='friends', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='directmessageuser',
            name='me',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='me', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='receiver_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiver_users', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='directmessage',
            name='sender_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sender_users', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='chatroomuser',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatroom', to='chatroom.subcategory'),
        ),
        migrations.AddField(
            model_name='chatroomuser',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatroom_users', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='chatroommodel',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='chatroommodel',
            name='participants',
            field=models.ManyToManyField(blank=True, help_text='Users participating in this chat room', related_name='chat_rooms', to=settings.AUTH_USER_MODEL, verbose_name='Participants'),
        ),
        migrations.AddField(
            model_name='chatroommodel',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AddField(
            model_name='category',
            name='country',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chatroom', to='chatroom.country'),
        ),
        migrations.AddField(
            model_name='calllog',
            name='caller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_calls', to=settings.AUTH_USER_MODEL, verbose_name='Caller'),
        ),
        migrations.AddField(
            model_name='calllog',
            name='chat_room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='call_logs', to='chatroom.chatroommodel', verbose_name='Chat Room'),
        ),
        migrations.AddField(
            model_name='calllog',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_calls', to=settings.AUTH_USER_MODEL, verbose_name='Receiver'),
        ),
        migrations.AddIndex(
            model_name='textmessage',
            index=models.Index(fields=['chat_room', 'sent_at'], name='chat_text_m_chat_ro_10e77a_idx'),
        ),
        migrations.AddIndex(
            model_name='textmessage',
            index=models.Index(fields=['sender', 'sent_at'], name='chat_text_m_sender__6dbb4f_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='subcategory',
            unique_together={('category', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='state',
            unique_together={('country', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='readreceipt',
            unique_together={('message', 'user')},
        ),
        migrations.AlterUniqueTogether(
            name='directmessageuser',
            unique_together={('me', 'friends')},
        ),
        migrations.AddIndex(
            model_name='chatroommodel',
            index=models.Index(fields=['room_type'], name='chat_rooms_room_ty_c8c67a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('country', 'name')},
        ),
    ]
