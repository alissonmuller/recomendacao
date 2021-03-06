# coding: utf-8

import hashlib
import json
import os
import subprocess
import urllib

from django.conf import settings
from django.core.cache import caches
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import strip_tags, escape
from django.views.generic import TemplateView
from django.views.generic.base import TemplateResponseMixin
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_xml.renderers import XMLRenderer

from auxiliares import funcoes_auxiliares as aux
from recomendacao.const import APP_NAME, ENCODING, CSE_ID, MAX_SIZE_SOBEK_OUTPUT
from recomendacao.forms import FormText
from recomendacao.search import GoogleSearchCse, GoogleSearchCseMarkup, GoogleSearchCseSeleniumMarkupImg
from recomendacao.serializers import SerializerText


def strip_escape(text):
    text = strip_tags(text)
    #text = escape(text)
    return text


def encode_string(string):
    return string.encode(ENCODING)


def decode_string(string):
    return string.decode(ENCODING)


def serialize_render(data, renderer_class):
    renderer = renderer_class()
    return renderer.render(data)


class TemplateViewContext(TemplateView):
    extra_context = {}

    def get_context_data(self, request, **kwargs):
        context = super(TemplateViewContext, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        self.get_request_data(request, context)
        return context

    def get_request_data(self, request, context):
        request_data_json = request.GET.get('data')
        if request_data_json:
            request_data = json.loads(request_data_json)
            context.update(request_data)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)


class TemplateViewContextPost(TemplateViewContext):
    http_method_names = ['post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def get_request_data(self, request, context):
        request_data_json = request.body
        if request_data_json:
            request_data = json.loads(request_data_json)
            context.update(request_data)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)


class TemplateViewBusca(TemplateViewContext):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        form = FormText()

        context.update({
            'form': form,
        })
        context.update(csrf(request))
        return render(request, self.template_name, context)


class EnviaTextoV1(TemplateResponseMixin, APIView):
    def post(self, request, format=None):
        serializer = SerializerText(data=request.data)
        if serializer.is_valid():
            self.request_data = serializer.data
            self.input_hash = hashlib.sha224(request.path_info + unicode(self.request_data)).hexdigest()
            response_data = self.get_response_data(request)
            return Response(response_data, status=status.HTTP_200_OK, template_name=self.template_name)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST, exception=True)

    def get_response_data(self, request):
        cache = caches['default']
        cache_reload = self.request_data.get('cache_reload')
        if cache.get(self.input_hash):
            json_response_data = self.read_response_data_file(self.input_hash, JSONRenderer.format)
            response_data = json.loads(json_response_data)
        else:
            response_data = self.process_text(request)
            cache.set(self.input_hash, True, cache_reload)
        return response_data

    def process_text(self, request):
        text = self.request_data['text']
        text = strip_escape(text)
        text = encode_string(text)
        response_data = {}

        sobek_output = self.run_sobek(text)
        while len(sobek_output.split()) > MAX_SIZE_SOBEK_OUTPUT:
            sobek_output = self.run_sobek(sobek_output)
        response_data['sobek_output'] = decode_string(sobek_output).split()

        response_data['text_hash'] = self.input_hash
        self.serialize_response_data(response_data)
        return response_data

    def run_sobek(self, text):
        sobek_path = os.path.join(settings.BASE_DIR, 'misc', 'webServiceSobek_Otavio.jar')

        try:
            quoted_text = urllib.quote(text)
            sobek_command = ['java', '-Dfile.encoding=' + ENCODING, '-jar', encode_string(sobek_path), '-b', '-t', '"' + encode_string(quoted_text) + '"']
            sobek_output = subprocess.check_output(sobek_command)
        except subprocess.CalledProcessError:
            text += ' ' + text

            quoted_text = urllib.quote(text)
            sobek_command = ['java', '-Dfile.encoding=' + ENCODING, '-jar', encode_string(sobek_path), '-b', '-t', '"' + encode_string(quoted_text) + '"']
            sobek_output = subprocess.check_output(sobek_command)

        sobek_output = sobek_output.replace('\n', ' ')

        return sobek_output

    def serialize_response_data(self, response_data):
        xml_response_data = serialize_render(response_data, XMLRenderer)
        self.create_response_data_file(xml_response_data, self.input_hash, XMLRenderer.format)
        json_response_data = serialize_render(response_data, JSONRenderer)
        self.create_response_data_file(json_response_data, self.input_hash, JSONRenderer.format)

    def create_response_data_file(self, response_data, text_hash, file_format):
        filename = text_hash + '.' + file_format
        aux.make_sure_path_exists(settings.FILES_ROOT)
        with open(os.path.join(settings.FILES_ROOT, filename), 'wb') as response_data_file:
            response_data_file.write(response_data)
            response_data_file.close()

    def read_response_data_file(self, text_hash, file_format):
        filename = text_hash + '.' + file_format
        aux.make_sure_path_exists(settings.FILES_ROOT)
        with open(os.path.join(settings.FILES_ROOT, filename), 'rb') as response_data_file:
            response_data = response_data_file.read()
            response_data_file.close()
        return response_data


class EnviaTextoV2(EnviaTextoV1):
    def process_text(self, request):
        text = self.request_data['text']
        text = strip_escape(text)
        text = encode_string(text)
        response_data = {}

        sobek_output = self.run_sobek(text)
        while len(sobek_output.split()) > MAX_SIZE_SOBEK_OUTPUT:
            sobek_output = self.run_sobek(sobek_output)
        search_input = sobek_output
        results_list = self.run_xgoogle(search_input, request)
        response_data['sobek_output'] = decode_string(sobek_output).split()
        response_data['results_list'] = results_list

        response_data['text_hash'] = self.input_hash
        self.serialize_response_data(response_data)
        return response_data

    def run_xgoogle(self, search_input, request):
        gs = GoogleSearchCse(search_input, user_agent=request.META['HTTP_USER_AGENT'], lang='pt-br', tld='com.br', cx=CSE_ID)
        results = gs.get_results()

        results_list = []
        for res in results:
            result_dict = {}

            result_dict['title'] = res.title
            result_dict['url'] = res.url
            result_dict['snippet'] = res.desc

            results_list.append(result_dict)

        return results_list


class EnviaTextoV3(EnviaTextoV2):
    def process_text(self, request):
        text = self.request_data['text']
        text = strip_escape(text)
        text = encode_string(text)
        mode = self.request_data.get('mode')
        images = self.request_data.get('images')
        response_data = {}

        if mode == 'sobek':
            sobek_output = self.run_sobek(text)
            while len(sobek_output.split()) > MAX_SIZE_SOBEK_OUTPUT:
                sobek_output = self.run_sobek(sobek_output)
            response_data['sobek_output'] = decode_string(sobek_output).split()
        elif mode == 'google':
            search_input = text
            results_list = self.run_xgoogle(search_input, request, images)
            response_data['results_list'] = results_list
        else:
            sobek_output = self.run_sobek(text)
            while len(sobek_output.split()) > MAX_SIZE_SOBEK_OUTPUT:
                sobek_output = self.run_sobek(sobek_output)
            search_input = sobek_output
            results_list = self.run_xgoogle(search_input, request, images)
            response_data['sobek_output'] = decode_string(sobek_output).split()
            response_data['results_list'] = results_list

        response_data['text_hash'] = self.input_hash
        self.serialize_response_data(response_data)
        return response_data

    def run_xgoogle(self, search_input, request, images):
        if not images:
            gs = GoogleSearchCseMarkup(search_input, user_agent=request.META['HTTP_USER_AGENT'], lang='pt-br', tld='com.br', cx=CSE_ID)
        else:
            gs = GoogleSearchCseSeleniumMarkupImg(search_input, user_agent=request.META['HTTP_USER_AGENT'], lang='pt-br', tld='com.br', cx=CSE_ID)
        results = gs.get_results()

        results_list = []
        for res in results:
            result_dict = {}

            result_dict['title'] = res.title
            result_dict['url'] = res.url
            result_dict['snippet'] = res.desc

            result_dict['title_markup'] = res.title_markup
            result_dict['url_markup'] = res.url_markup
            result_dict['snippet_markup'] = res.desc_markup

            if images:
                result_dict['img'] = getattr(res, 'img', None)

            results_list.append(result_dict)

        return results_list
